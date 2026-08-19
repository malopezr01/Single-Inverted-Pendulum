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

    homingState = homingDerecha();

    if (homingState != HomingState::OK)
    {
        Serial.println("Error durante homing derecha.");
        emergencyStop();
        return false;
    }

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

    const long railPosition = tmc.getSPIPosition();
    const long centerTarget = railPosition / 2;

    tmc.setRampMode(POS);
    tmc.targetPosition(centerTarget);
    tmc.setAcceleration(500);
    tmc.setSpeed(5000);

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

    digitalWrite(EN, HIGH); // Deshabilitar motor

    tmc.actualPosition(0);
    tmc.targetPosition(0);

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
    if (Serial.available() > 0)
    {
        char command = Serial.read();

        Serial.print("RX command: ");
        Serial.println(command);

        switch (command)
        {
        case 'R':
        case 'r':
            if (systemState == SystemState::READY)
            {
                Serial.println("R received -> resume = true");
                resume = true;
            }
            break;

        case 'S':
        case 's':
            Serial.println("S received -> resume = false");
            resume = false;
            break;

        case 'X':
        case 'x':
            Serial.println("X received -> EMERGENCY STOP");
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
        case SystemState::INIT: break;
        case SystemState::HOMING: break;
        case SystemState::READY: updateReadyState(); break;
        case SystemState::RUNNING: updateRunningState(); break;
        case SystemState::FAULT: updateFaultState(); break;
    }
}

void Pendulum::updateReadyState()
{
    tmc.setSpeed(0);

    if (resume)
    {
        if (fabsf(encoder.getTheta()) >= THETA_MAX)
        {
            resume = false;
            Serial.println("Pendulo fuera del rango de seguridad.");
            return;
        }

        initializeObserver();

        lastCycleTime = micros();
        controlMode = ControlMode::LQR;
        systemState = SystemState::RUNNING;

        tmc.setSpeed(V_MAX * speedRatio);
        digitalWrite(EN, LOW); // Enable motor

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

    if (fabsf(encoder.getTheta()) >= THETA_MAX)
    {
        tmc.setSpeed(0);
        resume = false;
        controlMode = ControlMode::NONE;
        systemState = SystemState::READY;

        Serial.println("Control fuera de rango de seguridad...");
        return;
    }

    uint64_t now = micros();
    dt = now - lastCycleTime;
    if (dt >= 10000)
    {
        lastCycleTime = now;
        // At the beginning of cycle k:
        // x0, x2      -> measurements y_k
        // u           -> previous control u_(k-1)
        // xhat        -> previous estimated state
        //
        // Observer updates estimate to xhat_k.
        // Controller then computes and applies u_k.
        updateMeasurements();
        updateObserver();
        updateControl();
    }
    else
    {
        return;
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
    cuenta += dt * 1e-6f;
}

void Pendulum::updateObserver()
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

void Pendulum::updateControl()
{
    switch (controlMode)
    {
        case ControlMode::LQR:
            u = computeLQR();
            break;
        case ControlMode::SWING_UP:
            //u = computeSwingUp();
            break;
        case ControlMode::NONE:
        default:
            u = 0.0f;
            break;          
    }

    // Mandar u al motor
    setAccelerationPendulum(u);
}

float Pendulum::computeLQR()
{
    return -(K[0] * x0
           + K[1] * xhat[1]
           + K[2] * x2
           + K[3] * xhat[3]);
}

void Pendulum::setAccelerationPendulum(float a)
{
  if (a > aMax)
    a = aMax;

  if (a < -aMax)
    a = -aMax;

  if (fabsf(x2) >= xMaxHard)
  {
    tmc.setSpeed(0);
    systemState = SystemState::READY;
    resume = false;
    return;
  }

  if (xhat[3] > 0 &&
      (x2 + 0.5f * xhat[3] * xhat[3] / aMax > xMax))
  {
    a = -aMax;
  }
  else if (xhat[3] < 0 &&
           (x2 - 0.5f * xhat[3] * xhat[3] / aMax < -xMax))
  {
    a = aMax;
  }

  if (a < 0)
    tmc.setRampMode(CCW);
  else
    tmc.setRampMode(CW);

  tmc.setAccelerationMax(
      fabsf(a * accelerationRatio));
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
        Serial.print(xhat[1], 4);

        Serial.print(" x=");
        Serial.print(x2, 4);

        Serial.print(" xDotObs=");
        Serial.print(xhat[3], 4);

        Serial.print(" xDotXActual=");
        Serial.print(x3, 4);

        Serial.print(" u=");
        Serial.print(u, 4);

        Serial.print(" state=");
        Serial.print(static_cast<int>(systemState));

        Serial.print(" mode=");
        Serial.println(static_cast<int>(controlMode));
    }
}
