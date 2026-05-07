#include <Arduino.h>
#include "mecanum.h"

// --- Tune these to match your robot's actual speed/geometry ---
#define DRIVE_SPEED   150   // PWM 0-255
#define TURN_SPEED    120   // PWM 0-255
#define DRIVE_MS     1500   // ms to travel one side of the square
#define TURN_MS       700   // ms to rotate ~90 degrees
#define PAUSE_MS      300   // brief stop between moves

void squareDrive() {
    for (int side = 0; side < 4; side++) {
        // Forward
        setWheels(DRIVE_SPEED, DRIVE_SPEED, DRIVE_SPEED, DRIVE_SPEED);
        delay(DRIVE_MS);
        stopWheels();
        delay(PAUSE_MS);

        // Rotate clockwise ~90°
        setWheels(TURN_SPEED, -TURN_SPEED, -TURN_SPEED, TURN_SPEED);
        delay(TURN_MS);
        stopWheels();
        delay(PAUSE_MS);
    }
}

// --- Serial command listener ---
// Format: "MOVE <fl> <fr> <bl> <br>\n"  (values -255..255)
void handleSerial() {
    if (Serial.available() == 0) return;

    String line = Serial.readStringUntil('\n');
    line.trim();

    if (!line.startsWith("MOVE")) return;

    int fl, fr, bl, br;
    int parsed = sscanf(line.c_str(), "MOVE %d %d %d %d", &fl, &fr, &bl, &br);
    if (parsed == 4) {
        setWheels(fl, fr, bl, br);
        Serial.println("OK");
    } else {
        Serial.println("ERR bad format");
    }
}

void setup() {
    Serial.begin(115200);
    motorInit();
    delay(500);

    Serial.println("mobile-robo opencr ready");
    squareDrive();
    Serial.println("square done — waiting for commands");
}

void loop() {
    handleSerial();
}
