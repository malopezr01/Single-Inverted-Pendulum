/*
* Library for controlling 2 channels rotary encoder with interrupts.
* Created by Miguel Angel López, 10th August 2026.
*/

#include <FinalCarrera.h>
void FinalCarrera::begin(uint8_t pinA, uint8_t pinB) {
  F1 = pinA; // Store pin numbers for channel A and B
  F2 = pinB; 
  pinMode(F1, INPUT_PULLUP); // Set channel A pin as input with pull-up resistor
  pinMode(F2, INPUT_PULLUP); // Set channel B pin as input with pull-up resistor
  F1State = (digitalRead(F1) == LOW);
  F2State = (digitalRead(F2) == LOW);
  // Attach interrupts for both channels to handle changes in state
  attachInterruptArg(digitalPinToInterrupt(F1), handleInterruptF1, this, FALLING); 
  attachInterruptArg(digitalPinToInterrupt(F2), handleInterruptF2, this, FALLING); 
}

void FinalCarrera::setFinalCarreraEnabled(bool enabled) {
  // Enable or disable the FinalCarrera by attaching or detaching interrupts
  if (enabled) {
    attachInterruptArg(digitalPinToInterrupt(F1), handleInterruptF1, this, FALLING);
    attachInterruptArg(digitalPinToInterrupt(F2), handleInterruptF2, this, FALLING);
  } else {
    detachInterrupt(digitalPinToInterrupt(F1));
    detachInterrupt(digitalPinToInterrupt(F2));
  }
}

void IRAM_ATTR FinalCarrera::handleInterruptF1(void* arg)
{
    FinalCarrera* self = static_cast<FinalCarrera*>(arg);
    self->F1State = true;
}

void IRAM_ATTR FinalCarrera::handleInterruptF2(void* arg)
{
    FinalCarrera* self = static_cast<FinalCarrera*>(arg);
    self->F2State = true;
}

bool FinalCarrera::getF1State()
{
  return F1State;
}

bool FinalCarrera::getF2State()
{
  return F2State;
}

void FinalCarrera::resetF1State()
{
  F1State = false;
}

void FinalCarrera::resetF2State()
{
  F2State = false;
}