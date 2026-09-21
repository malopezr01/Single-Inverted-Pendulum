import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from experiment_logger import ExperimentLogger
from experiment_session import ExperimentSession


class DynamicLoggerTests(unittest.TestCase):
    def test_column_order_metadata_frequency_and_pause(self):
        with tempfile.TemporaryDirectory() as tmp, patch('experiment_logger.time.monotonic',return_value=10) as clock:
            logger=ExperimentLogger(tmp, port='/dev/test', baudrate=115200)
            filename=logger.start(['energy','Time','uNN','state'])
            for t in (1,1.01): logger.write(dict(Time=t,energy=12,uNN=4,state=3))
            logger.pause()
            for t in (8,8.01): logger.write(dict(Time=t,energy=13,uNN=5,state=3))
            clock.return_value=15
            logger.stop('Finished by user')
            with open(filename) as f: rows=list(csv.reader(f))
            self.assertEqual(rows[0],['energy','Time','uNN','state'])
            self.assertEqual(rows[1],['12','1','4','3'])
            meta=json.loads(Path(filename).with_name('metadata.json').read_text())
            self.assertEqual(meta['sample_count'],4)
            self.assertEqual(meta['duration_seconds'],5)
            self.assertAlmostEqual(meta['estimated_acquisition_hz'],100)
            self.assertEqual(meta['port'],'/dev/test')
            self.assertEqual(meta['baudrate'],115200)
            self.assertEqual(meta['status'],'completed')
            self.assertEqual(meta['stop_reason'],'Finished by user')
            self.assertIsNotNone(meta['finished_at'])

    def test_checkpoints_mismatch_and_atomic_metadata_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            logger=ExperimentLogger(tmp)
            filename=logger.start(['Time','energy'])
            path=Path(filename).with_name('metadata.json')
            for i in range(50): logger.write(dict(Time=i/100,energy=i))
            checkpoint=path.read_text()
            self.assertEqual(json.loads(checkpoint)['sample_count'],50)
            self.assertEqual(json.loads(checkpoint)['status'],'recording')
            with self.assertRaises(ValueError): logger.write(dict(Time=1,energy=1,other=2))
            with patch('experiment_logger.os.replace',side_effect=OSError('disk full')):
                with self.assertRaises(OSError): logger.stop()
            self.assertFalse(logger.active)
            self.assertIsNone(logger.csv_file)
            self.assertEqual(path.read_text(),checkpoint)

    def test_header_rotation_and_repeated_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            events=[]
            session=ExperimentSession(lambda *e:events.append(e),tmp,port='test',baudrate=115200)
            session.start()
            try:
                header=['Time','state','energy']
                session.submit('header',header)
                session.submit('data',dict(Time=0,state=3,energy=1))
                session.submit('header',header)
                session.submit('data',dict(Time=.01,state=3,energy=2))
                session.submit('header',['uNN','energy','state','Time'])
                session.submit('data',dict(Time=.02,state=3,energy=3,uNN=4))
                session.submit('data',dict(Time=.03,state=2,energy=3,uNN=4))
                session.finish_when_ready()
                session._queue.join()
            finally: session.close()
            files=sorted(Path(tmp).glob('*/data.csv'))
            self.assertEqual(len(files),2)
            metadata=[json.loads(p.with_name('metadata.json').read_text()) for p in files]
            self.assertEqual([m['sample_count'] for m in metadata],[2,1])
            self.assertEqual(metadata[0]['stop_reason'],'Telemetry HEADER changed')
            self.assertEqual(metadata[1]['signals'],['uNN','energy','state','Time'])
            self.assertFalse(any(e[0]=='error' for e in events))
            with files[1].open() as f: self.assertEqual(list(csv.reader(f))[1],['4','3','3','0.02'])

    def test_failed_start_and_undefined_frequency(self):
        with tempfile.TemporaryDirectory() as tmp:
            logger=ExperimentLogger(tmp)
            with patch.object(logger,'_save_metadata',side_effect=OSError('full')):
                with self.assertRaises(OSError): logger.start(['state'])
            self.assertIsNone(logger.csv_file)
            self.assertFalse(logger.active)
            filename=logger.start(['state'])
            logger.write({'state':3});logger.stop('FAULT')
            meta=json.loads(Path(filename).with_name('metadata.json').read_text())
            self.assertIsNone(meta['estimated_acquisition_hz'])
            self.assertEqual(meta['stop_reason'],'FAULT')

if __name__=='__main__':unittest.main()
