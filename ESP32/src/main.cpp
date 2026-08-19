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
│ obtener θ̇                   │
│ leer/calcular x             │
│ obtener ẋ                   │
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
#include <Pendulum.h>

Pendulum pendulum;

void setup()
{
  /*==== Inicializar hardware ====*/
  Serial.begin(115200);
  delay(1500);

  pendulum.begin();

}

void loop()
{
  pendulum.update();
}