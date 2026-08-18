/*
* Library for controlling 2 channels rotary encoder with interrupts.
* Created by Miguel Angel López, 10th August 2026.
*/
#include <Arduino.h>
class FinalCarrera {
  private:
    uint8_t F1; // Pin for Final Carrera 1
    uint8_t F2; // Pin for Final Carrera 2
    volatile bool F1State; // State of FinalCarrera1
    volatile bool F2State; // State of FinalCarrera2
    volatile uint32_t F1ChangeTime = 0;
    volatile uint32_t F2ChangeTime = 0;
    volatile bool F1Pending = false;
    volatile bool F2Pending = false;
    static void IRAM_ATTR handleInterruptF1(void* arg); // Interrupt handler for FinalCarrera1
    static void IRAM_ATTR handleInterruptF2(void* arg); // Interrupt handler for FinalCarrera2
  public:
    void begin(uint8_t pinA, uint8_t pinB); // Initialize the FinalCarrera with specified pins
    void setFinalCarreraEnabled(bool enabled); // Enable/Disable the interrupts for the FinalCarrera
    bool getF1State(); // Return the state of the FC1
    void resetF1State(); // Reset the state of the FC1
    bool getF2State(); // Return the state of the FC2
    void resetF2State(); // Reset the state of the FC2
};