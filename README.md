# Single Inverted Pendulum

Physical inverted-pendulum platform designed and built from scratch for experimentation with embedded control, state estimation and data-driven control methods.

> **Project status:** the physical platform is operational. LQR balancing, state estimation and a first swing-up implementation are working on the real system. Mechanical refinement, energy-based swing-up and learning-based control are the next development stages.

## Overview

This repository contains the complete development of a real cart-pole inverted pendulum, including the electronics, custom PCB, embedded firmware, control design, experiment tooling and mechanical integration.

The project is intentionally treated as an engineering platform rather than a simulation exercise. The objective is not only to stabilize an ideal model, but to understand and solve the problems that appear when control algorithms are deployed on real hardware: finite rail travel, friction and stiction, sensor limitations, mechanical tolerances, actuator constraints and controller transitions.

### Current capabilities

- ✅ Physical cart-pole system built and operational
- ✅ Custom control electronics and PCB designed in KiCad
- ✅ PCB manufactured and assembled for the project
- ✅ ESP32-C3 embedded controller
- ✅ Stepper motor actuation through TMC5160
- ✅ Pendulum angle measurement using a quadrature encoder
- ✅ Automatic cart homing
- ✅ Linearized state-space model
- ✅ Discrete state observer
- ✅ LQR upright stabilization
- ✅ Swing-up v1 with automatic transition to LQR
- ✅ Rail-limit handling during swing-up and balancing
- ✅ Python GUI, serial telemetry and experiment logging
- 🔄 Mechanical refinement of the pivot and encoder coupling
- 🔄 Energy-based swing-up
- ⏳ Data-driven identification and neural-network control experiments

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

> Photos, PCB renders and assembly images will be added here as the public documentation is built.

## Control architecture

The current embedded controller combines different control modes around a common state-machine architecture.

### LQR balancing

Around the upright equilibrium, the system uses a linearized model with the state vector

\[
x = [\theta,\; \dot{\theta},\; x,\; \dot{x}]^T
\]

and an LQR state-feedback law.

The measured pendulum angle and cart position are combined with a discrete observer to estimate the state variables required by the controller.

Detailed mathematical derivations are intentionally kept outside this README. The existing control notes can be found in [`Documentation/apuntes_pendulo_invertido_LQR.md`](Documentation/apuntes_pendulo_invertido_LQR.md).

### Swing-up v1

The first swing-up implementation is complete and working on the physical system.

The controller accelerates the cart according to the pendulum motion and includes braking logic based on the available rail distance. Once the pendulum enters the LQR capture region with sufficiently low angular velocity, control automatically transitions to the LQR stabilizer.

The inverse transition is also implemented: if the pendulum leaves the LQR operating region, the controller can return to swing-up mode.

This first implementation establishes a functional baseline. Future work will focus on energy-based swing-up, improved rail usage and more systematic tuning.

## Real-world engineering issues

A central part of this project is documenting the difference between the ideal mathematical system and the physical plant.

The current platform has exposed several practical limitations that are being investigated rather than hidden:

- **Pivot friction and stiction.** Small friction around the upright equilibrium can produce a limit-cycle-like behaviour and reduce repeatability.
- **Finite cart travel.** Swing-up strategies must explicitly account for the limited rail length rather than assuming unlimited cart motion.
- **Mechanical precision.** Pivot geometry, encoder coupling and zero-position repeatability directly affect control performance.
- **Actuator constraints.** Acceleration, speed and stopping distance must be included in the real controller logic.
- **Controller transitions.** Moving reliably between swing-up and LQR requires explicit angle and angular-velocity capture conditions.

These issues are part of the engineering value of the project and will be documented through dedicated experiments and mechanical iterations.

## Experiment and telemetry tooling

A Python application is used to interact with the embedded controller and capture experiments.

The current toolset includes:

- serial communication with the ESP32;
- start, stop and emergency-stop commands;
- real-time visualization;
- experiment logging;
- telemetry parsing;
- storage of measured signals for later analysis.

The application lives in [`Python/`](Python/).

The intention is to evolve it into a lightweight control-experiment scope where new telemetry signals can be added with minimal changes to the Python side.

## Repository structure

```text
.
├── ESP32/          Embedded firmware and real-time control
├── Python/         Telemetry, GUI and experiment tools
├── Octave/         Control design and LQR tuning scripts
├── PCB/            KiCad project, custom libraries and fabrication files
├── Documentation/  Mathematical and technical notes
└── README.md
```

The existing source-code structure will be kept largely intact. Public-facing technical documentation will be added incrementally as experiments and design iterations mature.

## Development roadmap

The pendulum is intended as the first platform in a broader personal control-systems development programme.

### Current platform

- [x] Build the first physical cart-pole platform
- [x] Design and manufacture custom electronics
- [x] Implement homing and embedded system state machine
- [x] Develop the linear model and LQR controller
- [x] Implement state estimation
- [x] Validate upright balancing on real hardware
- [x] Implement swing-up v1
- [ ] Improve pivot mechanics and reduce stiction
- [ ] Improve encoder coupling and zero repeatability
- [ ] Develop and validate energy-based swing-up
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

## Documentation philosophy

The repository will evolve together with the hardware. Experimental results, failed assumptions, mechanical limitations and redesign decisions will be documented alongside successful controller implementations.

The goal is to make the engineering process visible: **model → design → implementation → experiment → problem → diagnosis → improvement**.
