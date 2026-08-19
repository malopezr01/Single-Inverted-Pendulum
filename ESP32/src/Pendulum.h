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
#define STOP 3

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
    LQR_FRICTION,
    SWING_UP
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

    FinalCarrera fc;
    Encoder encoder;
    TMC tmc;

    SystemState systemState = SystemState::INIT;
    HomingState homingState = HomingState::OK;
    ControlMode controlMode = ControlMode::NONE;

    // ========================================================================
    // Initialization
    // ========================================================================

    // Functions
    void initializeHardware();
    void configureMotor();
    bool performHoming();
    void initializePendulumReference();
    void enterReadyState();

    // ========================================================================
    // Homing
    // ========================================================================

    // Functions
    HomingState homingIzquierda();
    HomingState homingDerecha();
    HomingState homingCentro();

    // Variables
    //bool FC1State = false;
    //bool FC2State = false;
    uint64_t homingCycleTime = 0;
    static constexpr uint32_t HOMING_TIMEOUT_MS = 20000; // ms
    static constexpr long HOMING_TOLERANCE = 40;         // microsteps (~1 mm)

    // ========================================================================
    // Serial communication
    // ========================================================================

    // Functions
    bool checkSerialResume();
    bool checkSerialCommand();
    void sendTelemetry();

    // Variables
    bool resume = false;
    uint32_t lastTelemetry = 0;

    // ========================================================================
    // Measured system states
    // ========================================================================

    // Variables
    float x0 = PI;   // Pendulum angle [rad]
    float x2 = 0.0f; // Cart position [m]
    float x3 = 0.0f; // Cart velocity [m/s]
    float lastx3 = 0.0f;
    float a_xActual = 0.0f;
    int32_t xActual = 0;
    int32_t lastxActual = 0;

    // ========================================================================
    // State observer
    // ========================================================================

    // Variables
    float xhat[4] = {0.0f, 0.0f, 0.0f, 0.0f};
    float xhat_next[4] = {0.0f, 0.0f, 0.0f, 0.0f};
    const float Ad[4][4] = {
        {1.002280415304319f, 0.01000760022935386f, 0.0f, 0.0f},
        {0.4562563249884429f, 1.002280415304319f, 0.0f, 0.0f},
        {0.0f, 0.0f, 1.0f, 0.01f},
        {0.0f, 0.0f, 0.0f, 1.0f}};
    const float Bd[4] = {0.0002324582369336554f, 0.04650930937700743f, 0.00005f, 0.01f};
    const float K[4] = {69.50536056155524f, 9.862435668785068f, -21.4997927630159f, -18.31987099561388f};
    const float Lobs[4][2] = {
        {0.8017105895712615f, 0.0f},
        {16.6469923450831f, 0.0f},
        {0.0f, 0.1860729471918576f},
        {0.0f, 1.017038197658804f}};
    float eTheta = 0.0f;
    float eX = 0.0f;

    // ========================================================================
    // Control
    // ========================================================================

    // Functions
    void initializeObserver();
    void updateStateMachine();
    void updateReadyState();
    void updateRunningState();
    void updateFaultState();
    void updateMeasurements();
    void updateObserver();
    void updateControl();
    float computeLQR();
    void setAccelerationPendulum(float a);
    

    // Variables
    float u = 0.0f;
    float xMax = 0.15f;                                     // Soft cart limit [m]
    float xMaxHard = 0.20f;                                 // Hard cart limit [m]
    float aMax = 5.0f;                                      // Maximum acceleration [m/s²]
    static constexpr float THETA_MAX = 10.0f * PI / 180.0f; // [rad]
    static constexpr float V_MAX = 1.0f;                    // [m/s]

    // ========================================================================
    // Timing
    // ========================================================================

    // Variables
    uint64_t lastCycleTime = 0;
    float dt = 0.0f;
    float cuenta = 0.0f;

    // ========================================================================
    // Motor conversion factors
    // ========================================================================

    const float distanceRatio = circunferenciaPolea / (motorSteps * motorMicrosteps);
    const float accelerationRatio = 0.01527f / distanceRatio;
    const float speedRatio = (16777216.0f / 12000000.0f) / distanceRatio;
};