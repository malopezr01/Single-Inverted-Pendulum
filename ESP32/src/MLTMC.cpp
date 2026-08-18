/*
* TMC.cpp - Implementation of TMC class for controlling TMC5160 stepper motor driver via SPI.
 * Created by Magdi Laoun, July 2025.
 */
#include <MLTMC.h>
#include <SPI.h>

void TMC::begin(uint8_t sck_, uint8_t  mosi_, uint8_t  miso_, uint8_t cs_, uint8_t en_) {
  cs = cs_;
  en = en_;
  sck = sck_;
  mosi = mosi_;
  miso = miso_;
  pinMode(cs, OUTPUT);
  pinMode(en, OUTPUT);
  digitalWrite(cs, HIGH);
  digitalWrite(en, LOW);
  SPI.begin(sck, miso, mosi);
  SPI.setDataMode(SPI_MODE0);
}
void TMC::init(float iHold_, float iRun_, float mStep_) {
  setConfiguration(mStep_);
  setCurrent(iHold_, iRun_);
  setRampMode(0);
  actualPosition(0);
  targetPosition(0);
  setAcceleration(2000);
  setSpeed(40000);
}
uint8_t TMC::statVal;
void TMC::setChopConf(uint32_t mStep_) {
  uint32_t TOFF = 3;
  uint32_t HSTRT = 4;
  uint32_t HEND = 1;
  uint32_t TBL = 2;
  uint32_t TPFD = 0;
  uint32_t value = TOFF<<0
                  | HSTRT<<4
                  | HEND<<7
                  | TBL<<15
                  | TPFD<<20
                  | mStep_<<24;
  uint8_t instruction = CHOPCONF | WRITE;
  transferData(instruction, value);
}
void TMC::setCurrent(float iHold_, float iRun_) {
  uint32_t iH = 31/2 * iHold_;
  uint32_t iR = 31/2 * iRun_;
  Serial.print(iR);
  uint32_t delay = 6;
  uint32_t value = iH | iR << 8 | delay << 16;
  uint8_t instruction = IHOLD_IRUN | WRITE;
  transferData(instruction, value);
}
void TMC::setTPowerDown(){
  uint32_t value = 10;
  uint8_t instruction = TPOWERDOWN | WRITE;
  transferData(instruction, value);
}
void TMC::setConfiguration(uint32_t mStep_) {
    setChopConf(mStep_); //Set microstepping to 1/16
    setTPowerDown();
    setGlobalConf();
    setTimePwmThrs();
}
void TMC::setGlobalConf() {
  uint32_t en_pwm_mode = 1;
  uint32_t value = en_pwm_mode<<2;
  uint8_t instruction = GCONF | WRITE;
  transferData(instruction, value);
}
void TMC::setGlobalScaler(uint8_t scaler_) {
  uint8_t instruction = GLOBALSCALER | WRITE;
  transferData(instruction, scaler_);
}
void TMC::setTimePwmThrs() {
  uint32_t value = 500;
  uint8_t instruction = TPWMTHRS | WRITE;
  transferData(instruction, value);
}
void TMC::setAcceleration1(uint32_t value) {
  uint8_t instruction = A1 | WRITE;
  transferData(instruction, value);
}
void TMC::setSpeed1(uint32_t value) {
  uint8_t instruction = V1 | WRITE;
  transferData(instruction, value);
}
void TMC::setAccelerationMax(uint32_t value) {
  uint8_t instruction = AMAX | WRITE;
  transferData(instruction, value);
}
void TMC::setSpeedMax(uint32_t value) {
  uint8_t instruction = VMAX | WRITE;
  transferData(instruction, value);
}
void TMC::setDeceleration1(uint32_t value) {
  uint8_t instruction = D1 | WRITE;
  transferData(instruction, value);
}
void TMC::setDecelerationMax(uint32_t value) {
  uint8_t instruction = DMAX | WRITE;
  transferData(instruction, value);
}
void TMC::setSpeedStop() {
  uint32_t value = 100;
   uint8_t instruction = VSTOP | WRITE;
  transferData(instruction, value);
}
void TMC::setRampMode(uint32_t mode) {
  uint8_t instruction = RAMPMODE | WRITE;
  transferData(instruction, mode);
}
void TMC::setAcceleration(uint32_t value) {
  setAcceleration1(value);
  setAccelerationMax(value);
  setDeceleration1(value);
  setDecelerationMax(value);
  setSpeed1(0);
  setSpeedStop();
}

void TMC::setSpeed(uint32_t value) {
  setSpeedMax(value);
}
void TMC::targetPosition(int32_t value) {
  uint8_t instruction = XTARGET | WRITE;
  uint8_t *data =( uint8_t *) malloc(BUFFER_SIZE);
  data[4] = (value >> 0) & 0xFF;
  data[3] = (value >> 8) & 0xFF;
  data[2] = (value >> 16) & 0xFF;
  data[1] = (value >> 24) & 0xFF; 
  data[0] = XTARGET | WRITE;
  digitalWrite(cs, LOW);
  SPI.transfer(data, 5);
  digitalWrite(cs, HIGH);
  free(data);
}
void TMC::actualPosition(int32_t value) {
  //setRampMode(0);
  uint8_t instruction = XACTUAL | WRITE;
  transferData(instruction, value);
}
void TMC::transferData(uint8_t instruction, uint32_t value) {
  uint8_t *data =( uint8_t *) malloc(BUFFER_SIZE);
  data[4] = (value >> 0) & 0xFF;
  data[3] = (value >> 8) & 0xFF;
  data[2] = (value >> 16) & 0xFF;
  data[1] = (value >> 24) & 0xFF;
  data[0] = instruction | WRITE;
  digitalWrite(cs, LOW);
  SPI.transfer(data, 5);
  digitalWrite(cs, HIGH);
  free(data);
}
int16_t TMC::getSPISpeed() {
  uint8_t *data =( uint8_t *) malloc(BUFFER_SIZE);
  getSPIValue(VACTUAL, data);
  int16_t value = int16_t(data[4]) | (int16_t(data[3]) << 8);
  free(data);
  return value;
}
long TMC::getSPIPosition() {
   uint8_t *data =( uint8_t *) malloc(BUFFER_SIZE);
  getSPIValue(XACTUAL, data);
  long value = long(data[4]) | (long(data[3]) << 8) | (long(data[2]) << 16) | (long(data[1]) << 24);
  free(data);
  return value;
}
void TMC::getSPIValue(uint8_t instruction, uint8_t *data){
  data[0] = instruction;
  digitalWrite(cs, LOW);
  SPI.transfer(data, BUFFER_SIZE);
  digitalWrite(cs, HIGH);
  data[0] = instruction;
  digitalWrite(cs, LOW);
  SPI.transfer(data, BUFFER_SIZE);
  digitalWrite(cs, HIGH);
  int16_t value = int16_t(data[4]) | (int16_t(data[3]) << 8);
}