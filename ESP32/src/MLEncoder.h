/*
* Library for controlling 2 channels rotary encoder with interrupts.
* Created by Magdi Laoun, 19th July 2025.
* 20th July 2025: Added static instance for interrupt handling.
*/
#include <Arduino.h>
class Encoder {
  private:
    uint8_t cha; // Pin for channel A
    uint8_t chb; // Pin for channel B
    volatile long position; // Current position of the encoder
    volatile bool aState; // State of channel A
    volatile bool bState; // State of channel B
    static constexpr float COUNTS_PER_REV = 4000.0f;
    static void IRAM_ATTR handleInterruptA(void* arg); // Interrupt handler for channel A
    static void IRAM_ATTR handleInterruptB(void* arg); // Interrupt handler for channel B
    void IRAM_ATTR update(bool channelA); // Update the position based on the state of the channels
  public:
    void begin(uint8_t pinA, uint8_t pinB); // Initialize the encoder with specified pins
    long getPosition(); // Get the current position of the encoder
    float getTheta(); // Get the current angle of the encoder
    void resetPosition(); // Reset the encoder position to zero
    void actualPosition(float value); // Set the encoder position to the specified value
    void setEncoderEnabled(bool enabled); // Enable or disable the encoder
};