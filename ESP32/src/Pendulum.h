// This file was originally written by a human and has been reorganized by an AI.

#pragma once

#include <Arduino.h>
#include <FinalCarrera.h>
#include <MLEncoder.h>
#include <MLTMC.h>
// ============================================================================
// Hardware configuration
// ============================================================================

#define EN GPIO_NUM_10
#define CS GPIO_NUM_7
#define MISO GPIO_NUM_5
#define MOSI GPIO_NUM_6
#define SCK GPIO_NUM_4
#define CHA GPIO_NUM_0
#define CHB GPIO_NUM_1
#define F1 GPIO_NUM_3
#define F2 GPIO_NUM_2

// ============================================================================
// TMC operating modes
// ============================================================================

#define POS 0
#define CW 1
#define CCW 2
//#define STOP 3

// ============================================================================
// Mechanical configuration
// ============================================================================

#define motorMicrosteps 16
#define motorSteps 200
#define circunferenciaPolea (40.0f * 0.002f)

// ============================================================================
// System states
// ============================================================================

enum class SystemState
{
    INIT,
    HOMING,
    READY,
    RUNNING,
    FAULT
};

enum class HomingState
{
    OK,
    TIMEOUT,
    LIMIT_ERROR
};

enum class ControlMode
{
    NONE,
    LQR,
    SWING_UP = 2
};

// ============================================================================
// Pendulum
// ============================================================================

class Pendulum
{
public:
    // ========================================================================
    // Public interface
    // ========================================================================
    void begin();
    void update();
    void emergencyStop();

private:
    // ========================================================================
    // Dependencies
    // ========================================================================

    Encoder encoder;
    FinalCarrera fc;
    TMC tmc;

    // ========================================================================
    // Initialization
    // ========================================================================

    void initializeHardware();
    void configureMotor();
    void initializePendulumReference();

    // ========================================================================
    // Homing
    // ========================================================================

    bool performHoming();
    HomingState homingIzquierda();
    HomingState homingDerecha();
    HomingState homingCentro();

    HomingState homingState = HomingState::OK;
    static constexpr long HOMING_TARGET = -6000;
    static constexpr long HOMING_TOLERANCE = 40; // microsteps (~1 mm)
    static constexpr uint32_t HOMING_TIMEOUT_MS = 20000;
    uint64_t homingCycleTime = 0;

    // ========================================================================
    // Serial communication
    // ========================================================================

    bool checkSerialCommand();
    void sendTelemetryHeader();
    void sendTelemetryHeaderPeriodic();
    void sendTelemetry();

    bool resume = false;
    uint32_t lastTelemetry = 0;
    uint32_t lastTelemetryHeader = 0;

    // ========================================================================
    // Measured system states
    // ========================================================================

    void updateMeasurements();

    float x0 = PI; // Pendulum angle [rad]
    float x2 = 0.0f; // Cart position [m]
    float x3 = 0.0f; // Cart velocity [m/s]
    int32_t lastxActual = 0;
    int32_t xActual = 0;

    // ========================================================================
    // State observer
    // ========================================================================

    void initializeObserver();
    void updateObserver();

    bool observerInitialized = false;
    const float Ad[4][4] = {
        {1.002280415304319f, 0.01000760022935386f, 0.0f, 0.0f},
        {0.4562563249884429f, 1.002280415304319f, 0.0f, 0.0f},
        {0.0f, 0.0f, 1.0f, 0.01f},
        {0.0f, 0.0f, 0.0f, 1.0f}};
    const float Bd[4] = {0.0002324582369336554f, 0.04650930937700743f, 0.00005f, 0.01f};
    float eTheta = 0.0f;
    float eX = 0.0f;
    const float Lobs[4][2] = {
        {0.8017105895712615f, 0.0f},
        {16.6469923450831f, 0.0f},
        {0.0f, 0.1860729471918576f},
        {0.0f, 1.017038197658804f}};
    float xhat[4] = {0.0f, 0.0f, 0.0f, 0.0f};
    float xhat_next[4] = {0.0f, 0.0f, 0.0f, 0.0f};

    // ========================================================================
    // Control / orchestration
    // ========================================================================

    void updateStateMachine();
    void enterReadyState();
    void updateReadyState();
    void updateRunningState();
    void updateFaultState();
    void updateControl();
    float saturate(float value, float limit);
    float sign(float value)


    ControlMode controlMode = ControlMode::NONE;
    SystemState systemState = SystemState::INIT;
    float u = 0.0f;
    static constexpr float V_MAX = 2.0f; // Shared cart speed limit [m/s]

    // ========================================================================
    // LQR control
    // ========================================================================

    float computeLQR();
    float setAccelerationLQR(float a);

    static constexpr float A_MAX = 15.0f;
    const float K[4] = {69.50536056155524f, 9.862435668785068f, -21.4997927630159f, -18.31987099561388f};

    // ========================================================================
    // Swing-up control
    // ========================================================================

    float computeSwingUp();
    float setAccelerationSwingUp(float a);

    static constexpr float SWING_UP_ACCEL = 5.0f;

    // ========================================================================
    // Swing-up control / energy
    // ========================================================================

    float E = 0.0f;
    float E0 = 0.01f;
    const float g = 9.81;
    const float J = 0.0016095;
    static constexpr float K_ENERGY = 50.0f;
    const float ml = 0.0074800;

    // ========================================================================
    // Swing-up control / switching
    // ========================================================================

    static constexpr float SWITCHING_THRESHOLD = 0.01f;
    static constexpr float THETA_LQR_ENTER = 8.0f * PI / 180.0f;
    static constexpr float THETA_LQR_EXIT = 15.0f * PI / 180.0f;
    static constexpr float THETA_MAX = 10.0f * PI / 180.0f;
    static constexpr float THETADOT_LQR_ENTER = 5.0f;
    int32_t singSwitch = 1;

    // ========================================================================
    // Swing-up control / angular velocity estimation
    // ========================================================================

    float thetaDotSwingUp = 0.0f;
    float thetaPreviousVelocity = 0.0f;
    static constexpr uint32_t THETADOT_SAMPLE_MS = 10;
    uint32_t thetaVelocityTime = 0;

    // ========================================================================
    // Cart travel safety
    // ========================================================================

    void checkLimitSwitchSafety();

    float xMax = 0.15f; // Soft cart limit [m]

    // ========================================================================
    // Timing
    // ========================================================================

    float cuenta = 0.0f;
    float dt = 0.0f;
    uint64_t lastCycleTime = 0;

    // ========================================================================
    // Motor conversion factors
    // ========================================================================

    // Expand the distance factor here to keep initialization independent of member order.
    const float accelerationRatio = 0.01527f / (circunferenciaPolea / (motorSteps * motorMicrosteps));
    const float distanceRatio = circunferenciaPolea / (motorSteps * motorMicrosteps);
    const float speedRatio = (16777216.0f / 12000000.0f) / distanceRatio;
};
