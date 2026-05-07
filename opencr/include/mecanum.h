#pragma once
#include <Arduino.h>

// Motor pin assignments — adjust to match your OpenCR wiring
// OpenCR has onboard motor driver outputs on pins A0–A3 (or use DYNAMIXEL)
// These are PWM + direction pins for a generic H-bridge setup.
// Replace with your actual driver API if using Dynamixel or a different driver.

#define M1_PWM  2   // FL
#define M1_DIR  3
#define M2_PWM  4   // FR
#define M2_DIR  5
#define M3_PWM  6   // BL
#define M3_DIR  7
#define M4_PWM  8   // BR
#define M4_DIR  9

inline void motorInit() {
    int pwmPins[] = {M1_PWM, M2_PWM, M3_PWM, M4_PWM};
    int dirPins[] = {M1_DIR, M2_DIR, M3_DIR, M4_DIR};
    for (int i = 0; i < 4; i++) {
        pinMode(pwmPins[i], OUTPUT);
        pinMode(dirPins[i], OUTPUT);
    }
}

// Drive a single motor: speed -255..255 (negative = reverse)
inline void driveMotor(uint8_t pwmPin, uint8_t dirPin, int speed) {
    if (speed >= 0) {
        digitalWrite(dirPin, HIGH);
        analogWrite(pwmPin, constrain(speed, 0, 255));
    } else {
        digitalWrite(dirPin, LOW);
        analogWrite(pwmPin, constrain(-speed, 0, 255));
    }
}

// Set all four wheels at once
// Layout:
//   FL (M1)  FR (M2)
//   BL (M3)  BR (M4)
//
// Forward:           fl+ fr+ bl+ br+
// Clockwise rotate:  fl+ fr- bl- br+
// Strafe right:      fl+ fr- bl+ br-
inline void setWheels(int fl, int fr, int bl, int br) {
    driveMotor(M1_PWM, M1_DIR, fl);
    driveMotor(M2_PWM, M2_DIR, fr);
    driveMotor(M3_PWM, M3_DIR, bl);
    driveMotor(M4_PWM, M4_DIR, br);
}

inline void stopWheels() {
    setWheels(0, 0, 0, 0);
}
