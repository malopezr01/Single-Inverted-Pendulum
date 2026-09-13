#include <Pendulum.h>

void Pendulum::begin()
{
    systemState = SystemState::INIT;
    controlMode = ControlMode::NONE;

    initializeHardware();
    configureMotor();

    if (!performHoming())
    {
        return;
    }

    initializePendulumReference();
    initializeObserver();

    enterReadyState();
}

void Pendulum::update()
{
    checkSerialCommand();
    updateStateMachine();
    sendTelemetry();
}

void Pendulum::initializeHardware()
{
    fc.begin(F1, F2);
    encoder.begin(CHA, CHB);
    encoder.setEncoderEnabled(false);
    tmc.begin(SCK, MOSI, MISO, CS, EN);
}

void Pendulum::configureMotor()
{
    uint8_t microstepConfig;

    switch (motorMicrosteps)
    {
    case 256:
        microstepConfig = 0;
        break;
    case 128:
        microstepConfig = 1;
        break;
    case 64:
        microstepConfig = 2;
        break;
    case 32:
        microstepConfig = 3;
        break;
    case 16:
        microstepConfig = 4;
        break;
    case 8:
        microstepConfig = 5;
        break;
    case 4:
        microstepConfig = 6;
        break;
    case 2:
        microstepConfig = 7;
        break;
    case 1:
        microstepConfig = 8;
        break;

    default:
        microstepConfig = 4; // 1/16
        break;
    }

    tmc.init(0.05f, 0.4f, microstepConfig);

    digitalWrite(EN, HIGH); // Disable motor

    tmc.setAcceleration(300);
    tmc.setSpeed(1500);
}

bool Pendulum::performHoming()
{
    systemState = SystemState::HOMING;

    homingState = homingIzquierda();

    if (homingState != HomingState::OK)
    {
        Serial.println("Error durante homing izquierda.");
        emergencyStop();
        return false;
    }

    /*homingState = homingDerecha();

    if (homingState != HomingState::OK)
    {
        Serial.println("Error durante homing derecha.");
        emergencyStop();
        return false;
    }*/

    homingState = homingCentro();

    if (homingState != HomingState::OK)
    {
        Serial.println("Error durante homing centro.");
        emergencyStop();
        return false;
    }

    return true;
}

void Pendulum::initializePendulumReference()
{
    Serial.println("Definiendo posicion inicial del pendulo...");

    delay(5000);

    encoder.actualPosition(2000);
    encoder.setEncoderEnabled(true);

    Serial.println("Posicion inicial del pendulo definida.");

    delay(1000);
}

void Pendulum::initializeObserver()
{
    xActual = tmc.getSPIPosition();

    x0 = encoder.getTheta();
    x2 = xActual * distanceRatio;
    x3 = 0.0f;

    xhat[0] = x0;
    xhat[1] = 0.0f;
    xhat[2] = x2;
    xhat[3] = 0.0f;

    xhat_next[0] = xhat[0];
    xhat_next[1] = xhat[1];
    xhat_next[2] = xhat[2];
    xhat_next[3] = xhat[3];

    lastxActual = xActual;

    eTheta = 0.0f;
    eX = 0.0f;

    u = 0.0f;
    observerInitialized = true;
}

void Pendulum::enterReadyState()
{
    homingState = HomingState::OK;
    systemState = SystemState::READY;
    controlMode = ControlMode::NONE;

    tmc.setSpeed(0);
    resume = false;

    digitalWrite(EN, HIGH); // Disable Motor

    Serial.println("READY");
}

HomingState Pendulum::homingIzquierda()
{
    Serial.println(" Homing izquierda...");

    tmc.setRampMode(CCW);
    digitalWrite(EN, LOW); // Habilitar motor

    homingCycleTime = millis();

    while (!fc.getF2State())
    {
        if (millis() - homingCycleTime > HOMING_TIMEOUT_MS)
        {
            return HomingState::TIMEOUT;
        }
    }

    digitalWrite(EN, HIGH); // Deshabilitar motor

    fc.resetF2State();
    tmc.actualPosition(0);

    return HomingState::OK;
}

HomingState Pendulum::homingDerecha()
{
    Serial.println("Homing derecha...");

    tmc.setRampMode(CW);
    tmc.setAcceleration(500);
    tmc.setSpeed(5000);

    digitalWrite(EN, LOW); // Habilitar motor

    homingCycleTime = millis();

    while (!fc.getF1State())
    {
        if (millis() - homingCycleTime > HOMING_TIMEOUT_MS)
        {
            return HomingState::TIMEOUT;
        }

        if (tmc.getSPIPosition() > 19000)
        {
            tmc.setAcceleration(300);
            tmc.setSpeed(1500);
        }
    }

    digitalWrite(EN, HIGH); // Deshabilitar motor

    fc.resetF1State();

    return HomingState::OK;
}

HomingState Pendulum::homingCentro()
{
    Serial.println("Calculando centro...");

    // const long railPosition = tmc.getSPIPosition();
    // const long centerTarget = railPosition / 2;
    const long centerTarget = 11000;

    tmc.setRampMode(POS);
    tmc.targetPosition(centerTarget);
    tmc.setAcceleration(500);
    tmc.setSpeed(3000);

    digitalWrite(EN, LOW); // Habilitar motor

    homingCycleTime = millis();

    while (abs(tmc.getSPIPosition() - centerTarget) > HOMING_TOLERANCE)
    {
        if (millis() - homingCycleTime > HOMING_TIMEOUT_MS)
        {
            return HomingState::TIMEOUT;
        }

        delay(1);
    }

    tmc.actualPosition(0);
    tmc.targetPosition(HOMING_TARGET);

    homingCycleTime = millis();

    while (abs(tmc.getSPIPosition() - HOMING_TARGET) > HOMING_TOLERANCE)
    {
        if (millis() - homingCycleTime > HOMING_TIMEOUT_MS)
        {
            return HomingState::TIMEOUT;
        }

        delay(1);
    }

    digitalWrite(EN, HIGH); // Deshabilitar motor

    return HomingState::OK;
}

void Pendulum::emergencyStop()
{
    tmc.setRampMode(STOP);
    digitalWrite(EN, HIGH);

    resume = false;
    controlMode = ControlMode::NONE;
    systemState = SystemState::FAULT;

    Serial.println("EMERGENCY STOP - Motor deshabilitado");
}

bool Pendulum::checkSerialCommand()
{
    /*
     * Comandos válidos:
     *
     * R -> START
     * S -> STOP
     * X -> EMERGENCY STOP
     *
     * Sólo se aceptan MAYÚSCULAS.
     *
     * Esto es importante porque antes también aceptábamos:
     *
     * r
     * s
     * x
     *
     * y cualquier carácter espurio recibido por Serial
     * podía provocar una acción accidental.
     */

    if (Serial.available() > 0)
    {
        char command = Serial.read();

        /*
         * Ignoramos cualquier carácter que no sea
         * exactamente R, S o X.
         *
         * Por tanto:
         *
         * 'r' -> ignorado
         * 'H' -> ignorado
         * 'o' -> ignorado
         * '\n' -> ignorado
         */
        if (
            command != 'R' &&
            command != 'S' &&
            command != 'X')
        {
            return resume;
        }

        Serial.print("RX command: ");
        Serial.println(command);

        switch (command)
        {
            // =========================================
            // START
            // =========================================

        case 'R':

            /*
             * R sólo tiene efecto cuando el sistema
             * está realmente en READY.
             *
             * Si estamos en HOMING, RUNNING o FAULT
             * no hace absolutamente nada.
             */
            if (systemState == SystemState::READY)
            {
                Serial.println(
                    "R received -> resume = true");

                resume = true;
            }

            break;

            // =========================================
            // STOP
            // =========================================

        case 'S':

            Serial.println(
                "S received -> resume = false");

            resume = false;

            break;

            // =========================================
            // EMERGENCY STOP
            // =========================================

        case 'X':

            Serial.println(
                "X received -> EMERGENCY STOP");

            emergencyStop();

            break;
        }
    }

    return resume;
}

void Pendulum::updateStateMachine()
{
    switch (systemState)
    {
    case SystemState::INIT:
        break;
    case SystemState::HOMING:
        break;
    case SystemState::READY:
        updateReadyState();
        break;
    case SystemState::RUNNING:
        updateRunningState();
        break;
    case SystemState::FAULT:
        updateFaultState();
        break;
    }
}

void Pendulum::updateReadyState()
{
    tmc.setSpeed(0);

    if (resume)
    {
        initializeObserver();

        lastCycleTime = micros();

        swingUpKickDone = false;
        swingUpKickActive = false;
        swingUpKickStart = 0;
        thetaDotSwingUp = 0.0f;
        thetaPreviousVelocity = x0;
        thetaVelocityTime = millis();

        if (fabsf(encoder.getTheta()) < THETA_MAX)
        {
            controlMode = ControlMode::LQR;
            Serial.println("Starting in LQR mode");
        }
        else
        {
            controlMode = ControlMode::SWING_UP;
            OldSignSwitch = singSwitch;
            Serial.println("Starting in SWING_UP mode");
        }

        systemState = SystemState::RUNNING;

        tmc.setSpeed(V_MAX * speedRatio);
        digitalWrite(EN, LOW);

        Serial.println("RUNNING");
    }
}

void Pendulum::updateRunningState()
{
    if (!resume)
    {
        tmc.setSpeed(0);
        controlMode = ControlMode::NONE;
        systemState = SystemState::READY;
        return;
    }

    uint64_t now = micros();
    dt = now - lastCycleTime;

    if (dt >= 10000)
    {
        lastCycleTime = now;

        updateMeasurements();

        // Seleccionar controlador
        if (controlMode == ControlMode::SWING_UP)
        {
            if (fabsf(x0) < THETA_LQR_ENTER &&
                fabsf(thetaDotSwingUp) < THETADOT_LQR_ENTER)
            {
                observerInitialized = false;
                controlMode = ControlMode::LQR;

                Serial.println("SWING_UP -> LQR");
            }
        }
        else if (controlMode == ControlMode::LQR)
        {
            if (fabsf(x0) > THETA_LQR_EXIT)
            {
                controlMode = ControlMode::SWING_UP;
                OldSignSwitch = singSwitch;
                Serial.println("LQR -> SWING_UP");
            }
        }

        updateObserver();
        updateControl();
    }
}

void Pendulum::updateFaultState()
{
    // FAULT latched.
    // Only reset/reinitialization can leave this state.
}

void Pendulum::updateMeasurements()
{
    xActual = tmc.getSPIPosition();
    x0 = encoder.getTheta();
    x2 = xActual * distanceRatio;
    x3 = (xActual - lastxActual) * distanceRatio / (dt * 1e-6f);
    lastxActual = xActual;

    // Calcula la velocidad del pendulo por derivada cada 30 ms para el control de swing up.
    // Para LQR se utiliza la estimación del observador de estados

    uint32_t now = millis();

    if (now - thetaVelocityTime >= THETADOT_SAMPLE_MS)
    {
        float deltaThetaVelocity = x0 - thetaPreviousVelocity;

        if (deltaThetaVelocity > PI)
        {
            deltaThetaVelocity -= 2.0f * PI;
        }
        else if (deltaThetaVelocity < -PI)
        {
            deltaThetaVelocity += 2.0f * PI;
        }

        thetaDotSwingUp =
            deltaThetaVelocity /
            ((now - thetaVelocityTime) * 1e-3f);

        thetaPreviousVelocity = x0;
        thetaVelocityTime = now;
    }

    // E = 0.5 * J * thetaDotSwingUp * thetaDotSwingUp + ml * g * (cosf(x0) - 1.0f);
    singSwitch = (thetaDotSwingUp * cosf(x0) > SWITCHING_THRESHOLD) ? 1 : (thetaDotSwingUp * cosf(x0) < -SWITCHING_THRESHOLD) ? -1
                                                                                                                              : singSwitch;
    energySwitch = (singSwitch != OldSignSwitch) ? true : false;
    positionReached = fabs(xActual - xTarget) < SWITCHING_TOLERANCE ? true : false;
    cuenta += dt * 1e-6f;
}

void Pendulum::updateObserver()
{
    if (!observerInitialized)
    {
        xActual = tmc.getSPIPosition();

        x0 = encoder.getTheta();
        x2 = xActual * distanceRatio;

        xhat[0] = x0;
        xhat[1] = thetaDotSwingUp;
        xhat[2] = x2;
        xhat[3] = x3;

        xhat_next[0] = xhat[0];
        xhat_next[1] = xhat[1];
        xhat_next[2] = xhat[2];
        xhat_next[3] = xhat[3];

        lastxActual = xActual;

        eTheta = 0.0f;
        eX = 0.0f;

        u = 0.0f;
        observerInitialized = true;
    }
    else
    {
        // Calcular error del observador
        eTheta = x0 - xhat[0];
        eX = x2 - xhat[2];

        // Calcular siguiente estado del observador
        xhat_next[0] = Ad[0][0] * xhat[0] + Ad[0][1] * xhat[1] + Ad[0][2] * xhat[2] + Ad[0][3] * xhat[3] + Bd[0] * u + Lobs[0][0] * eTheta + Lobs[0][1] * eX;

        xhat_next[1] = Ad[1][0] * xhat[0] + Ad[1][1] * xhat[1] + Ad[1][2] * xhat[2] + Ad[1][3] * xhat[3] + Bd[1] * u + Lobs[1][0] * eTheta + Lobs[1][1] * eX;

        xhat_next[2] = Ad[2][0] * xhat[0] + Ad[2][1] * xhat[1] + Ad[2][2] * xhat[2] + Ad[2][3] * xhat[3] + Bd[2] * u + Lobs[2][0] * eTheta + Lobs[2][1] * eX;

        xhat_next[3] = Ad[3][0] * xhat[0] + Ad[3][1] * xhat[1] + Ad[3][2] * xhat[2] + Ad[3][3] * xhat[3] + Bd[3] * u + Lobs[3][0] * eTheta + Lobs[3][1] * eX;

        // Actualizar estado del observador
        xhat[0] = xhat_next[0];
        xhat[1] = xhat_next[1];
        xhat[2] = xhat_next[2];
        xhat[3] = xhat_next[3];
    }
}

void Pendulum::updateControl()
{
    switch (controlMode)
    {
    case ControlMode::LQR:
        u = computeLQR();
        break;
    case ControlMode::SWING_UP:
        u = computeSwingUp();
        break;
    case ControlMode::NONE:
    default:
        u = 0.0f;
        break;
    }
}

float Pendulum::computeLQR()
{
    uApplied = setAccelerationLQR(-(K[0] * x0 + K[1] * xhat[1] + K[2] * x2 + K[3] * xhat[3]));
    return uApplied;
}

float Pendulum::computeSwingUp()
{
    float a = (singSwitch > 0)
                  ? +SWING_UP_ACCEL
                  : -SWING_UP_ACCEL;

    const float brakingDistance =
        (x3 * x3) / (2.0f * SWING_UP_ACCEL);

    bool mustBrakeRight =
        a > 0.0f &&
        x3 > 0.0f &&
        (x2 + brakingDistance >= xMax);

    bool mustBrakeLeft =
        a < 0.0f &&
        x3 < 0.0f &&
        (x2 - brakingDistance <= -xMax);

    if (mustBrakeRight || mustBrakeLeft)
    {
        tmc.setSpeed(0);
        return 0.0f;
    }

    tmc.setSpeed(V_MAX * speedRatio);

    if (a > 0.0f)
        tmc.setRampMode(CW);
    else
        tmc.setRampMode(CCW);

    tmc.setAcceleration(
        fabsf(a * accelerationRatio));

    return a;
}

float Pendulum::setAccelerationLQR(float a)
{
    if (a > A_MAX)
        a = A_MAX;

    if (a < -A_MAX)
        a = -A_MAX;

    if (fabsf(x2) >= xMaxHard)
    {
        tmc.setSpeed(0);
        systemState = SystemState::READY;
        resume = false;
        return 0.0f;
    }

    if (x3 > 0 &&
        (x2 + 0.5f * x3 * x3 / A_MAX > xMax))
    {
        a = -A_MAX;
    }
    else if (x3 < 0 &&
             (x2 - 0.5f * x3 * x3 / A_MAX < -xMax))
    {
        a = A_MAX;
    }

    // IMPORTANTE: swing-up puede haber dejado speed = 0
    tmc.setSpeed(V_MAX * speedRatio);

    if (a < 0)
        tmc.setRampMode(CCW);
    else
        tmc.setRampMode(CW);

    tmc.setAcceleration(
        fabsf(a * accelerationRatio));

    return a;
}

void Pendulum::sendTelemetry()
{
    uint32_t now = millis();

    if (now - lastTelemetry >= 30)
    {
        lastTelemetry = now;

        Serial.print("Time=");
        Serial.print(cuenta, 4);

        Serial.print(" theta=");
        Serial.print(x0, 4);

        Serial.print(" thetaDot=");
        Serial.print(thetaDotSwingUp, 4);

        Serial.print(" x=");
        Serial.print(x2, 4);

        Serial.print(" xDotObs=");
        Serial.print(xhat[3], 4);

        Serial.print(" xDotXActual=");
        Serial.print(x3, 4);

        Serial.print(" u=");
        // Serial.print(-k * (E - E0) * sign(thetaDotSwingUp * cosf(x0)), 4);
        Serial.print(u, 4);

        Serial.print(" state=");
        Serial.print(static_cast<int>(systemState));

        Serial.print(" mode=");
        Serial.println(static_cast<int>(controlMode));
    }
}

float Pendulum::saturate(float value, float limit)
{
    if (value > limit)
        return limit;

    if (value < -limit)
        return -limit;

    return value;
}

float Pendulum::sign(float value)
{
    if (value > 0.0)
        return 1.0;

    if (value < 0.0)
        return -1.0;

    return 0.0;
}
