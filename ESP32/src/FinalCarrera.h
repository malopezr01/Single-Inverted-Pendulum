/*
* Library for controlling 2 channels rotary encoder with interrupts.
* Created by Miguel Angel López, 10th August 2026.
*/
#include <Arduino.h>
class FinalCarrera {
  private:
    uint8_t F1; // Pin for Final Carrera 1
    uint8_t F2; // Pin for Final Carrera 2
    volatile bool F1State; // Latched event from FinalCarrera1 interrupt
    volatile bool F2State; // Latched event from FinalCarrera2 interrupt
    volatile uint32_t F1ChangeTime = 0;
    volatile uint32_t F2ChangeTime = 0;
    volatile bool F1Pending = false;
    volatile bool F2Pending = false;
    static void IRAM_ATTR handleInterruptF1(void* arg); // Interrupt handler for FinalCarrera1
    static void IRAM_ATTR handleInterruptF2(void* arg); // Interrupt handler for FinalCarrera2
  public:
    void begin(uint8_t pinA, uint8_t pinB); // Initialize the FinalCarrera with specified pins
    void setFinalCarreraEnabled(bool enabled); // Enable/Disable the interrupts for the FinalCarrera
    bool getF1State(); // Return the latched interrupt event of FC1
    void resetF1State(); // Reset the latched event of FC1
    bool getF2State(); // Return the latched interrupt event of FC2
    void resetF2State(); // Reset the latched event of FC2
    bool isF1Pressed(); // Return the current physical state of FC1
    bool isF2Pressed(); // Return the current physical state of FC2
};