// Main sequence program for single inverted pendulum
/*
ENCENDER
   ↓
Inicializar hardware
   ↓
Comprobar que todo responde
   ↓
Homing izquierda
   ↓
Homing derecha
   ↓
Calcular centro
   ↓
Mover al centro
   ↓
Definir x = 0
   ↓
READY
   ↓
esperar orden de inicio
   ↓
┌─────────────────────────────┐
│ cada Ts                     │
│                             │
│ leer θ                      │
│ obtener θ̇                  │
│ leer/calcular x             │
│ obtener ẋ                  │
│                             │
│ comprobar seguridad         │
│                             │
│ u = -Kx                     │
│                             │
│ saturar u                   │
│ convertir u → TMC           │
│ aplicar                     │
│                             │
│ enviar telemetría           │
└─────────────────────────────┘
*/

#include <Arduino.h>
#include <FinalCarrera.h>
#include <MLEncoder.h>
#include <MLTMC.h>

#define EN GPIO_NUM_10
#define CS GPIO_NUM_7
#define MISO GPIO_NUM_5
#define MOSI GPIO_NUM_6
#define SCK GPIO_NUM_4
#define CHA GPIO_NUM_0
#define CHB GPIO_NUM_1
#define F1 GPIO_NUM_3
#define F2 GPIO_NUM_2
#define POS 0
#define CW 1
#define CCW 2
#define STOP 3
#define motorMicrosteps 16
#define circunferenciaPolea 40 * 0.002
#define RailLength 0.6
#define motorSteps 200

enum class SystemState
{
  INIT,
  HOMING,
  READY,
  CONTROL,
  FAULT
};

enum class HomingState
{
  OK,
  TIMEOUT,
  LIMIT_ERROR
};

FinalCarrera fc;
Encoder encoder;
TMC tmc;
SystemState systemState;
HomingState homingState;

HomingState homingIzquierda();
HomingState homingDerecha();
HomingState homingCentro();
bool checkSerialResume();
void checkSerialCommand();
void emergencyStop();
void setAcceleration(float a);

bool FC1State;
bool FC2State;
bool resume = false;
float x0 = PI;                                 // Variable to store the current position of the encoder
float x2 = 0;                                  // Variable to store the current position of the cart
float x3 = 0;                                  // Variable to store the current speed of the cart
uint64_t homingCycleTime = 0;                  // Variable to store time taken for one control cycle
uint64_t lastCycleTime = 0;                    // Variable to store time taken for one control cycle
const long tolerance = 40;                     // Tolerance for homing center position (microsteps) x = 40* (D/(200*motorMicrosteps)) = 1mm
const long waitingTime = 20000;                // Maximum time to wait for homing (ms)
float xhat[4] = {0.0f, 0.0f, 0.0f, 0.0f};      // Estimated state vector
float xhat_next[4] = {0.0f, 0.0f, 0.0f, 0.0f}; // Estimated state vector
float u = 0.0f;                                // Control input
float eTheta = 0.0f;                           // Error in theta
float eX = 0.0f;                               // Error in X
float xMax = 0.15f;                            // Maximum position (m)
float xMaxHard = 0.2f;                         // Maximum position (m)
float aMax = 5.0f;                             // Maximum acceleration (m/s^2)
const float thetaMax = 10.0f * PI / 180.0f;
const float distanceRatio = circunferenciaPolea / (motorSteps * motorMicrosteps);
const float accelerationRatio = 0.01527f / distanceRatio;
uint32_t lastTelemetry = 0;
const float speedRatio = (16777216.0f / 12000000.0f) / distanceRatio;
const float vMax = 1.0f; // m/s
float dt = 0;
int32_t xActual = 0;
int32_t lastxActual = 0;
float cuenta = 0;
float lastx3 = 0;
float a_xActual = 0;

const float Ad[4][4] = {
    {1.002280415304319f, 0.01000760022935386f, 0.0f, 0.0f},
    {0.4562563249884429f, 1.002280415304319f, 0.0f, 0.0f},
    {0.0f, 0.0f, 1.0f, 0.01f},
    {0.0f, 0.0f, 0.0f, 1.0f}};

const float Bd[4] = {0.0002324582369336554f, 0.04650930937700743f, 5e-05f, 0.01f};

const float K[4] = {69.50536056155524f, 9.862435668785068f, -21.4997927630159f, -18.31987099561388f};

const float Lobs[4][2] = {
    {0.8017105895712615f, -0.0f},
    {16.6469923450831f, -0.0f},
    {-0.0f, 0.1860729471918576f},
    {-0.0f, 1.017038197658804f}};

void setup()
{

  systemState = SystemState::INIT;

  /*==== Inicializar hardware ====*/
  Serial.begin(115200);
  delay(1500);

  fc.begin(F1, F2);
  encoder.begin(CHA, CHB);
  tmc.begin(SCK, MOSI, MISO, CS, EN);
  encoder.setEncoderEnabled(false);

  FC1State = fc.getF1State();
  FC2State = fc.getF2State();

  // MRES = 0 -> 256 microsteps en esta implementación.
  switch (motorMicrosteps)
  {
  case 256:
    tmc.init(0.05f, 0.4f, 0);
    break;
  case 128:
    tmc.init(0.05f, 0.4f, 1);
    break;
  case 64:
    tmc.init(0.05f, 0.4f, 2);
    break;
  case 32:
    tmc.init(0.05f, 0.4f, 3);
    break;
  case 16:
    tmc.init(0.05f, 0.4f, 4);
    break;
  case 8:
    tmc.init(0.05f, 0.4f, 5);
    break;
  case 4:
    tmc.init(0.05f, 0.4f, 6);
    break;
  case 2:
    tmc.init(0.05f, 0.4f, 7);
    break;
  case 1:
    tmc.init(0.05f, 0.4f, 8);
    break;
  default:
    tmc.init(0.05f, 0.4f, 4);
    break; // Default to microsteps = 16
  }

  digitalWrite(EN, HIGH); // Desabilita el motor
  tmc.setAcceleration(300);
  tmc.setSpeed(1500);

  systemState = SystemState::HOMING;
  homingState = HomingState::OK;

  /*==== Homing Izquierda ====*/
  homingState = homingIzquierda();
  if (homingState == HomingState::TIMEOUT)
  {
    systemState = SystemState::FAULT;
    Serial.println("Homing izquierda timeout. Verifique el sensor de fin de carrera.");
    while (true)
    {
      delay(1000); // Detener el programa en caso de error
    }
  }

  /*==== Homing Derecha ====*/
  homingState = homingDerecha();
  if (homingState == HomingState::TIMEOUT)
  {
    systemState = SystemState::FAULT;
    Serial.println("Homing derecha timeout. Verifique el sensor de fin de carrera.");
    while (true)
    {
      delay(1000); // Detener el programa en caso de error
    }
  }

  /*==== Calcular Centro ====*/
  homingState = homingCentro();
  if (homingState == HomingState::TIMEOUT)
  {
    systemState = SystemState::FAULT;
    Serial.println("Homing centro timeout. Verifique el motor.");
    while (true)
    {
      delay(1000); // Detener el programa en caso de error
    }
  }

  /*====   Definir x = 0 ====*/
  Serial.println("Definiendo posición inicial del pendulo...");
  delay(5000);
  encoder.actualPosition(2000);
  encoder.setEncoderEnabled(true);
  Serial.println("Posición inicial del pendulo definida.");

  delay(1000);

  /*==== READY ====*/
  // inicializa el vector de control
  xhat[0] = encoder.getTheta();
  xhat[1] = 0.0f;
  xhat[2] = tmc.getSPIPosition() * distanceRatio;
  xhat[3] = 0.0f;
  tmc.setSpeed(0);
  systemState = SystemState::READY;
  homingState = HomingState::OK;
  Serial.println("READY");
  digitalWrite(EN, LOW); // Habilitar el motor
  // delay(1000);

  // Serial.println("Esperando confirmación de inicio...");
  /*
  while (!checkSerialResume())
   {
     delay(1);
     Serial.print("theta=");
     Serial.println(encoder.getTheta(), 4);
   }
 */
  // systemState = SystemState::CONTROL;
  // Serial.println("CONTROL");
}

void loop()
{
  resume = checkSerialResume();
  if (!resume)
  {
    tmc.setSpeed(0);
    systemState = SystemState::READY;
  }
  else if (abs(encoder.getTheta()) >= thetaMax)
  {
    // tmc.setRampMode(STOP);
    tmc.setSpeed(0);

    // NO hacer esto aquí:
    // digitalWrite(EN, HIGH);

    systemState = SystemState::READY;
    resume = false;

    Serial.println("Control fuera de rango de seguridad...");
  }
  else
  {
    if (systemState != SystemState::CONTROL)
    {
      // Reinicializar observador al rearmar
      xActual = tmc.getSPIPosition();
      lastxActual = xActual;
      x0 = encoder.getTheta();
      xhat[0] = x0;
      xhat[1] = 0.0f;
      xhat[2] = xActual * distanceRatio;
      xhat[3] = 0.0f;
      x3 = 0.0f;

      tmc.setSpeed(vMax * speedRatio);

      lastCycleTime = micros();
      Serial.println("Control dentro del rango de seguridad...");
    }

    systemState = SystemState::CONTROL;
    digitalWrite(EN, LOW); // Habilitar el motor
    dt = micros() - lastCycleTime;

    if (dt >= 10000)
    {
      // Tomamos este instante como referencia del muestreo
      lastCycleTime = micros();

      // Leer Yk
      x0 = encoder.getTheta();

      xActual = tmc.getSPIPosition();
      x2 = xActual * distanceRatio;

      // Velocidad derivada de XACTUAL usando el dt que acaba de cumplirse
      x3 = (xActual - lastxActual) * distanceRatio / (dt * 1e-6f);
      lastxActual = xActual;

      cuenta += dt * 1e-6f;

      // Calcular error del observador
      eTheta = x0 - xhat[0];
      eX = x2 - xhat[2];
      

      // Calcular control u = -Kxhat  ¿Es necesario realimentar los estados del observador o basta con realimentar los originales y el estados estimado por el observador (theta speed)?
      u = -(K[0] * x0 + K[1] * xhat[1] + K[2] * x2 + K[3] * xhat[3]);

      // Mandar u al motor
      setAcceleration(u);

      // Calcular siguiente estado del observador
      xhat_next[0] =
          Ad[0][0] * xhat[0] + Ad[0][1] * xhat[1] + Ad[0][2] * xhat[2] + Ad[0][3] * xhat[3] + Bd[0] * u + Lobs[0][0] * eTheta + Lobs[0][1] * eX;

      xhat_next[1] =
          Ad[1][0] * xhat[0] + Ad[1][1] * xhat[1] + Ad[1][2] * xhat[2] + Ad[1][3] * xhat[3] + Bd[1] * u + Lobs[1][0] * eTheta + Lobs[1][1] * eX;

      xhat_next[2] =
          Ad[2][0] * xhat[0] + Ad[2][1] * xhat[1] + Ad[2][2] * xhat[2] + Ad[2][3] * xhat[3] + Bd[2] * u + Lobs[2][0] * eTheta + Lobs[2][1] * eX;

      xhat_next[3] =
          Ad[3][0] * xhat[0] + Ad[3][1] * xhat[1] + Ad[3][2] * xhat[2] + Ad[3][3] * xhat[3] + Bd[3] * u + Lobs[3][0] * eTheta + Lobs[3][1] * eX;

      // Actualizar estado del observador
      xhat[0] = xhat_next[0];
      xhat[1] = xhat_next[1];
      xhat[2] = xhat_next[2];
      xhat[3] = xhat_next[3];
    }
  }

  if (millis() - lastTelemetry >= 30)
  {
    lastTelemetry = millis();

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
    Serial.println(u, 4);
  }
}

HomingState homingIzquierda()
{
  Serial.println("Homing izquierda...");

  tmc.setRampMode(CCW);
  digitalWrite(EN, LOW); // Habilitar el motor
  homingCycleTime = millis();
  while (!fc.getF2State())
  {
    if (millis() - homingCycleTime > waitingTime)
    {
      emergencyStop();
      return HomingState::TIMEOUT;
    }
  }

  digitalWrite(EN, HIGH); // Desabilita el motor
  fc.resetF2State();
  tmc.actualPosition(0);
  return HomingState::OK;
}

HomingState homingDerecha()
{
  Serial.println("Homing derecha...");

  tmc.setRampMode(CW);
  tmc.setAcceleration(500);
  tmc.setSpeed(5000);
  digitalWrite(EN, LOW); // Habilitar el motor
  homingCycleTime = millis();
  while (!fc.getF1State())
  {
    if (millis() - homingCycleTime > waitingTime)
    {
      emergencyStop();
      return HomingState::TIMEOUT;
    }
    if (tmc.getSPIPosition() > 19000)
    {
      tmc.setAcceleration(300);
      tmc.setSpeed(1500);
    }
  }

  digitalWrite(EN, HIGH); // Desabilita el motor
  fc.resetF1State();
  return HomingState::OK;
}

HomingState homingCentro()
{
  Serial.println("Calculando centro...");
  long Rail_XActual = tmc.getSPIPosition();
  long centerTarget = Rail_XActual / 2;

  tmc.setRampMode(POS);
  tmc.targetPosition(centerTarget);
  tmc.setAcceleration(500);
  tmc.setSpeed(5000);
  digitalWrite(EN, LOW); // Habilitar el motor
  homingCycleTime = millis();
  while (abs(tmc.getSPIPosition() - centerTarget) > tolerance)
  {
    if (millis() - homingCycleTime > waitingTime)
    {
      emergencyStop();
      return HomingState::TIMEOUT;
    }
    delay(1);
  }

  digitalWrite(EN, HIGH); // Desabilita el motor

  tmc.actualPosition(0);
  tmc.targetPosition(0);
  return HomingState::OK;
}

void checkSerialCommand()
{
  if (Serial.available() > 0)
  {
    char command = Serial.read();

    if (command == 'X' || command == 'x')
    {
      Serial.println("STOP manual solicitado");
      emergencyStop();
    }
  }
}

bool checkSerialResume()
{
  if (Serial.available() > 0)
  {
    char command = Serial.read();

    if ((command == 'R' || command == 'r') && resume == false)
    {
      Serial.println("Start");
      resume = true;
    }
    if ((command == 'S' || command == 's') && resume == true)
    {
      Serial.println("Stop");
      resume = false;
    }
  }
  return resume;
}

void emergencyStop()
{
  tmc.setRampMode(STOP);
  digitalWrite(EN, HIGH); // Desabilita el motor

  systemState = SystemState::FAULT;

  Serial.println("EMERGENCY STOP - Motor deshabilitado");
}

void setAcceleration(float a)
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