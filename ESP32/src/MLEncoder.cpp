/*
* Library for controlling 2 channels rotary encoder with interrupts.
* Created by Magdi Laoun, 19th July 2025.
* 20th July 2025: Added static instance for interrupt handling.
*/
#include <MLEncoder.h>
void Encoder::begin(uint8_t pinA, uint8_t pinB) {
  cha = pinA; // Store pin numbers for channel A and B
  chb = pinB; 
  position = 0; // Initialize position to zero
  aState = digitalRead(cha); // Read initial state of channel A
  bState = digitalRead(chb); // Read initial state of channel B
  pinMode(cha, INPUT_PULLUP); // Set channel A pin as input with pull-up resistor
  pinMode(chb, INPUT_PULLUP); // Set channel B pin as input with pull-up resistor
  // Attach interrupts for both channels to handle changes in state
  attachInterruptArg(digitalPinToInterrupt(cha), handleInterruptA, this,  CHANGE); 
  attachInterruptArg(digitalPinToInterrupt(chb), handleInterruptB, this, CHANGE); 
}
long Encoder::getPosition() {
  return position; // Return the current position of the encoder
}

float Encoder::getTheta() {
  float theta = (static_cast<float>(position) / COUNTS_PER_REV) * 2.0f * PI; // Convert position to angle in radians

  while (theta >= PI)  theta -= 2.0f * PI;
  while (theta < -PI)  theta += 2.0f * PI;

  return theta; // Return the current angle of the encoder
}

void Encoder::resetPosition() {
  position = 0; // Reset the encoder position to zero
}

void Encoder::actualPosition(float value) {
  position = value; // Set the encoder position to the specified value
}

void Encoder::setEncoderEnabled(bool enabled) {
  // Enable or disable the encoder by attaching or detaching interrupts
  if (enabled) {
    attachInterruptArg(digitalPinToInterrupt(cha), handleInterruptA, this, CHANGE);
    attachInterruptArg(digitalPinToInterrupt(chb), handleInterruptB, this, CHANGE);
  } else {
    detachInterrupt(digitalPinToInterrupt(cha));
    detachInterrupt(digitalPinToInterrupt(chb));
  }
}
void IRAM_ATTR Encoder::handleInterruptA(void* arg) {
  Encoder* enc = static_cast<Encoder*>(arg); // Cast the argument to an Encoder pointer
  enc->update(true);
}
void IRAM_ATTR Encoder::handleInterruptB(void* arg) {
  Encoder* enc = static_cast<Encoder*>(arg); // Cast the argument to an Encoder pointer
  enc->update(false);
}
void IRAM_ATTR Encoder::update(bool channelA) {
  // Read the current state of both channels
  bool a = digitalRead(cha);
  bool b = digitalRead(chb);
  if (channelA) {
    if (a != aState) {
      position += (a == b) ? -1 : 1; // Update position based on the state of the channels
      aState = a;
    }
  } else {
    if (b != bState) {
      position += (a != b) ? -1 : 1; // Update position based on the state of the channels
      bState = b;
    }
  }
}