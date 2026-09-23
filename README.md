# Single Inverted Pendulum

Physical inverted-pendulum platform designed and built from scratch for experimentation with embedded control, state estimation and data-driven control methods.

> **Project status:** the physical platform is operational. LQR balancing, state estimation and energy-based swing-up with repeated LQR capture have been validated on the real system. Mechanical refinement, broader swing-up validation and learning-based control remain active development areas.

<p align="center">
  <img src="docs/assets/gifs/swingup_v1.gif" width="560" alt="Swing-up v1 transitioning into LQR balance">
</p>

<p align="center"><em>Swing-up v1 on the physical platform, followed by automatic capture by the LQR controller.</em></p>

## Overview

This repository contains the development of a real cart-pole inverted pendulum, including electronics, custom PCB, embedded firmware, control design, experiment tooling and mechanical integration.

The project is used as a practical control platform rather than only as a simulation exercise. The main interest is in what changes when the controller is deployed on real hardware: finite rail travel, friction and stiction, sensor limitations, mechanical tolerances, actuator constraints and controller transitions.

<p align="center">
  <img src="docs/assets/images/system/complete_system_overview.jpeg" width="650" alt="Complete inverted pendulum experimental platform">
</p>

### Current capabilities

- Physical cart-pole system built and operational
- Custom control electronics and PCB designed in KiCad
- PCB manufactured and assembled for the project
- ESP32-C3 embedded controller
- Stepper motor actuation through TMC5160
- Pendulum angle measurement using a quadrature encoder
- Cart homing against both end stops with physical switch checks
- Linearized state-space model
- Discrete state observer
- LQR upright stabilization
- Energy-based swing-up with automatic transition to LQR
- Rail-limit handling during swing-up and balancing
- Python GUI, serial telemetry and experiment logging

Current work:

- Pivot and encoder mechanics
- Transmission tensioning
- Energy-based swing-up tuning and validation across initial conditions
- Data-driven control experiments

## System architecture

The current system is divided into four main layers:

```text
Physical pendulum / cart
        │
        ▼
Sensors + actuator
Encoder + NEMA17 / TMC5160
        │
        ▼
ESP32-C3
Homing · State estimation · Swing-up · LQR · Safety
        │
        ▼
Serial telemetry
        │
        ▼
Python experiment tool
Visualization · Commands · Logging · Analysis
```

The control loop runs on the ESP32. The Python application is used as the supervisory and experiment interface rather than as part of the real-time controller.

## Hardware

This is a fully built physical system, not a software-only project.

The hardware development includes:

- component selection;
- ESP32-C3 control electronics;
- TMC5160 stepper motor driver;
- NEMA17 actuator;
- pendulum encoder interface;
- 24 V power system and DC conversion;
- end-stop integration for cart homing;
- custom schematic and PCB design;
- custom KiCad symbols and footprints;
- PCB routing and manufacturing files;
- PCB fabrication and assembly;
- wiring and full-system integration;
- mechanical cart and pendulum assembly.

The complete KiCad project, Gerbers and BOM-related files are available in [`PCB/`](PCB/).

### Custom PCB

The controller PCB was designed specifically for the platform and manufactured from the KiCad design files included in this repository.

The PCB design also contains notes for the next revision, including connector orientation, the encoder interface and driver-enable behaviour during reset or firmware upload. The latter records unwanted cart motion and proposes a 10 kΩ pull-up on the active-low TMC5160 enable input. This is a documented hardware correction to implement and verify, not a completed PCB revision.

<table>
<tr>
<td width="50%" align="center"><img src="docs/assets/images/pcb/pcb_layout.png" alt="KiCad PCB layout"><br><em>PCB layout in KiCad</em></td>
<td width="50%" align="center"><img src="docs/assets/images/pcb/pcb_fabricated_front.jpeg" alt="Fabricated controller PCB"><br><em>Fabricated PCB</em></td>
</tr>
</table>

The schematic and both sides of the fabricated board are preserved in [`docs/assets/images/pcb/`](docs/assets/images/pcb/), while the editable design and manufacturing files remain in [`PCB/`](PCB/).

### Mechanical prototype

The current mechanical platform is a first functional prototype. It is good enough to validate the control architecture, but it also makes the next mechanical tasks clear: reducing pivot friction, improving encoder coupling, adding a better transmission tensioning solution and improving repeatability.

<table>
<tr>
<td width="33%" align="center"><img src="docs/assets/images/mechanics/pivot_detail.jpg" alt="Pendulum pivot detail"><br><em>Pivot detail</em></td>
<td width="33%" align="center"><img src="docs/assets/images/mechanics/motor_detail.jpeg" alt="Stepper motor and transmission detail"><br><em>Motor and transmission</em></td>
<td width="33%" align="center"><img src="docs/assets/images/mechanics/encoder_detail.jpeg" alt="Pendulum encoder detail"><br><em>Encoder detail</em></td>
</tr>
</table>

## Control architecture

The embedded controller combines different control modes around a common state-machine architecture.

### LQR balancing

Around the upright equilibrium, the system uses a linearized model with the state vector

\[
x = [\theta,\; \dot{\theta},\; x,\; \dot{x}]^T
\]

and an LQR state-feedback law.

The measured pendulum angle and cart position are combined with a discrete observer to estimate the state variables required by the controller.

<p align="center">
  <img src="docs/assets/gifs/lqr_balance.gif" width="520" alt="LQR balancing on the physical pendulum">
</p>

Detailed mathematical derivations are kept outside this README. The current control notes are available in [`Documentation/apuntes_pendulo_invertido_LQR.md`](Documentation/apuntes_pendulo_invertido_LQR.md).

### Swing-up

The original swing-up v1 used fixed-amplitude bang-bang switching and was validated on the physical system. The animation above records that stage of development.

The implementation now included in `main` computes pendulum energy from angle and angular velocity and modulates acceleration using the energy error. The command is saturated at the swing-up acceleration limit, while the switching direction follows angular velocity and pendulum angle. Rail-distance braking and automatic LQR capture are retained.

The current capture conditions are an angle within 8° of upright and angular speed below 5 rad/s. The observer is reinitialized at capture; if the angle later exceeds 15°, control returns to swing-up. The control loop has a nominal 10 ms period.

Energy-based swing-up was validated on hardware with repeated transitions to stable LQR balance. Recovery across arbitrary initial conditions still needs broader characterization, and encoder cable routing remains a mechanical limitation.

### Homing and stopping

Homing visits the left and right end stops, establishes the cart reference and moves to the configured starting position. Each stage has a timeout. The firmware reads the physical switch levels during homing, clears historical switch events afterwards and checks that neither switch is held before enabling control. The current center reference is a fixed calibration value rather than a midpoint calculated from the measured rail travel.

A limit-switch event during `RUNNING` triggers an emergency stop. The emergency-stop routine first clears the TMC speed command, then disables the driver and enters a latched `FAULT` state; reset or reinitialization is required to leave it. Normal stop returns the controller to `READY`.

In `main`, homing starts during initialization. On `docs/public-project-presentation`, startup remains in `INIT` with the motor disabled until an explicit HOME command (`H`); HOME is accepted from `INIT` or `READY`. Both versions use `R` to start from `READY`, `S` to stop/pause and `X` for emergency stop.

## Real-world engineering issues

The physical system has exposed several limitations that are being investigated as part of the development process:

- **Pivot friction and stiction.** Small friction around the upright equilibrium can produce a limit-cycle-like behaviour and reduce repeatability.
- **Finite cart travel.** Swing-up strategies must explicitly account for the limited rail length rather than assuming unlimited cart motion.
- **Initial-condition sensitivity.** Energy-based swing-up has achieved repeated LQR capture, but its recovery range and sensitivity to initial phase still need systematic testing.
- **Mechanical precision.** Pivot geometry, encoder coupling and zero-position repeatability directly affect control performance. Encoder cable routing also needs a mechanical fix to avoid interference during motion.
- **Transmission tensioning.** The current transmission will be refined with a dedicated tensioning solution.
- **Actuator constraints.** Acceleration, speed and stopping distance have to be included in the real controller logic.
- **Controller transitions.** Moving reliably between swing-up and LQR requires explicit angle and angular-velocity capture conditions.

These points will be revisited as the mechanics and control strategy evolve.

## Experimental results

The control laws are tested on the physical platform rather than validated only in simulation. Recorded signals include pendulum angle and angular velocity, cart position, observer-estimated and position-derived cart velocity, control acceleration, controller mode and system state. The images below are retained examples from the earlier experiments; they are not presented as new measurements of the energy-based controller.

### Pendulum response

<p align="center">
  <img src="docs/assets/images/experiments/pendulum_state.png" width="760" alt="Pendulum angle and angular velocity during an experiment">
</p>

### Cart motion

<p align="center">
  <img src="docs/assets/images/experiments/cart_position.png" width="760" alt="Cart position during swing-up and balancing">
</p>

### Control action

<p align="center">
  <img src="docs/assets/images/experiments/control_action.png" width="760" alt="Applied control action during experiment">
</p>

The main README only shows a compact selection of plots. More detailed experiment reports will use a consistent structure: **Objective → Hypothesis → Setup → Method → Results → Discussion → Conclusion → Next step**.

## Experiment and telemetry tooling

A Python application is used to interact with the embedded controller and capture experiments.

<p align="center">
  <img src="docs/assets/images/experiments/python_gui.png" width="780" alt="Python telemetry and experiment GUI">
</p>

The current toolset includes:

- serial communication with the ESP32;
- start, stop and emergency-stop commands;
- real-time visualization;
- experiment logging;
- telemetry parsing;
- storage of measured signals for later analysis.

The application lives in [`Python/`](Python/).

In `main`, telemetry uses named `key=value` fields at a nominal 30 ms interval. The GUI displays angle, position and control-action traces, records samples while `RUNNING`, preserves an experiment across pause/resume and opens saved results when it finishes.

The `docs/public-project-presentation` branch also includes the newer experiment scope, which has not yet been merged into `main`:

- explicit HOME control and separate initialization, ready, running and fault states;
- `HEADER`/`DATA` telemetry with signal discovery and compatibility with legacy `key=value` frames;
- a signal selector, independent live plot windows and an adjustable visual history;
- recording separated from plot refresh, with additional signals retained in the CSV;
- one experiment directory containing `data.csv` and `metadata.json`, including signal names, timing, sample counts and the reason recording ended;
- saved-CSV viewing with selectable signals; a changed telemetry header starts a separate recording segment.

Only `RUNNING` samples are recorded; pausing preserves the current experiment. Further implementation details and verification instructions for this branch are in [`Python/ARCHITECTURE.md`](Python/ARCHITECTURE.md).

## Repository structure

```text
.
├── ESP32/          Embedded firmware and real-time control
├── Python/         Telemetry, GUI and experiment tools
├── Octave/         Control design and LQR tuning scripts
├── PCB/            KiCad project, custom libraries and fabrication files
├── Documentation/  Mathematical and technical notes
├── docs/assets/     Public-facing images, plots and animations
└── README.md
```

The source-code structure is being kept largely intact. Public-facing documentation will be added as the experiments and design iterations mature.

## Development roadmap

### Current platform

- [x] Build the first physical cart-pole platform
- [x] Design and manufacture custom electronics
- [x] Implement homing and embedded system state machine
- [x] Develop the linear model and LQR controller
- [x] Implement state estimation
- [x] Validate upright balancing on real hardware
- [x] Implement swing-up v1 based on bang-bang control
- [ ] Improve pivot mechanics and reduce stiction
- [ ] Improve encoder coupling and zero repeatability
- [ ] Add/improve mechanical transmission tensioning
- [x] Implement energy-based swing-up and validate repeated LQR capture on hardware
- [ ] Characterize energy-based swing-up across initial conditions and rail usage
- [ ] Fix encoder cable routing to avoid interference during motion
- [ ] Implement and verify the documented PCB reset/boot enable correction
- [ ] Improve recovery from arbitrary pendulum phase
- [ ] Formalize experimental test documentation

### Data-driven control

- [ ] Build datasets from real experiments
- [ ] Train a neural network to imitate the LQR controller
- [ ] Compare neural-network and LQR behaviour on recorded data
- [ ] Investigate hybrid LQR + neural-network control
- [ ] Explore residual learning
- [ ] Explore reinforcement learning on the platform

### Future platforms

- [ ] Double inverted pendulum
- [ ] More mechanically refined cart-pole versions
- [ ] Additional unstable control benchmarks
- [ ] Experimental platforms combining advanced control, embedded systems and machine learning

## Documentation approach

The repository will evolve together with the hardware. Experimental results, mechanical limitations and redesign decisions will be documented alongside the controller implementations.

The development path is kept visible: **model → design → implementation → experiment → problem → diagnosis → improvement**.
