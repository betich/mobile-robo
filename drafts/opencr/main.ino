#include <Dynamixel2Arduino.h>
#include <Servo.h>

#define DXL_SERIAL   Serial3
#define DEBUG_SERIAL Serial
const int DXL_DIR_PIN = 84;

#define RAD_PER_SEC_TO_RPM  (60.0/(2.0*M_PI))

const uint8_t DXL_ID_FL = 1;
const uint8_t DXL_ID_FR = 2;
const uint8_t DXL_ID_BL = 3;
const uint8_t DXL_ID_BR = 4;

const float DXL_PROTOCOL_VERSION = 2.0;

Dynamixel2Arduino dxl(DXL_SERIAL, DXL_DIR_PIN);
using namespace ControlTableItem;

float d = 0.097;
float l = 0.041;
float a = 0.0295;

const float MAX_LINEAR_SPEED = 0.5;
const float DEADZONE         = 0.08;

// Servo setup
Servo servoX;
Servo servoY;
#define SERVO_X_PIN 9
#define SERVO_Y_PIN 10

// Servo speed state (degrees per second, signed)
float servoX_speed = 0.0f;
float servoY_speed = 0.0f;
float servoX_pos   = 90.0f;
float servoY_pos   = 90.0f;

unsigned long lastServoUpdate = 0;
#define SERVO_UPDATE_MS 20   // 50 Hz servo update

// ── helpers ───────────────────────────────────────────────────────────────

float applyDeadzone(float v) {
  if (fabs(v) < DEADZONE) return 0.0f;
  return (v > 0) ? (v - DEADZONE) / (1.0f - DEADZONE)
                 : (v + DEADZONE) / (1.0f - DEADZONE);
}

// ── IK ───────────────────────────────────────────────────────────────────

void mecanum_IK(float u, float v, float r) {
  float inv_a = 1.0f / a;

  float w1 = inv_a * (u + v + (-d + l) * r);
  float w2 = inv_a * (u - v + (-d + l) * r);
  float w3 = inv_a * (u + v + ( d - l) * r);
  float w4 = inv_a * (u - v + ( d - l) * r);

  float rpm1 = w1 * RAD_PER_SEC_TO_RPM;
  float rpm2 = w2 * RAD_PER_SEC_TO_RPM;
  float rpm3 = w3 * RAD_PER_SEC_TO_RPM;
  float rpm4 = w4 * RAD_PER_SEC_TO_RPM;

  DEBUG_SERIAL.print("  FL:"); DEBUG_SERIAL.print(rpm1);
  DEBUG_SERIAL.print(" BL:");  DEBUG_SERIAL.print(rpm2);
  DEBUG_SERIAL.print(" BR:");  DEBUG_SERIAL.print(rpm3);
  DEBUG_SERIAL.print(" FR:");  DEBUG_SERIAL.println(rpm4);

  dxl.setGoalVelocity(DXL_ID_FL, rpm1, UNIT_RPM);
  dxl.setGoalVelocity(DXL_ID_BL, rpm2, UNIT_RPM);
  dxl.setGoalVelocity(DXL_ID_BR, rpm3, UNIT_RPM);
  dxl.setGoalVelocity(DXL_ID_FR, rpm4, UNIT_RPM);
}

// ── servo velocity update (called every loop) ─────────────────────────────

void updateServos() {
  unsigned long now = millis();
  if (now - lastServoUpdate < SERVO_UPDATE_MS) return;
  float dt = (now - lastServoUpdate) / 1000.0f;
  lastServoUpdate = now;

  servoX_pos += servoX_speed * dt;
  servoY_pos += servoY_speed * dt;

  servoX_pos = constrain(servoX_pos, 0.0f, 180.0f);
  servoY_pos = constrain(servoY_pos, 0.0f, 180.0f);

  servoX.write((int)servoX_pos);
  servoY.write((int)servoY_pos);
}

// ── command dispatcher ────────────────────────────────────────────────────
//
//  Commands (send via Serial Monitor, newline ending):
//
//    drive u v        — set mecanum wheel velocity (m/s)
//                       e.g.  "drive 0.3 0"
//                             "drive 0 -0.2"
//                             "drive 0 0"       (stop)
//
//    servo x_spd y_spd — set servo velocity (deg/s)
//                        e.g.  "servo 30 0"     (pan right)
//                              "servo 0 -20"    (tilt down)
//                              "servo 0 0"      (hold)
//
// ─────────────────────────────────────────────────────────────────────────

void handleCommand(String line) {
  line.trim();
  if (line.length() == 0) return;

  // ── drive u v ────────────────────────────────────────────────────────
  if (line.startsWith("drive ")) {
    String args = line.substring(6);
    args.trim();
    int sp = args.indexOf(' ');
    if (sp < 0) { DEBUG_SERIAL.println("ERR drive format: drive u v"); return; }

    String uStr = args.substring(0, sp);
    String vStr = args.substring(sp + 1);
    uStr.trim(); vStr.trim();

    float u = uStr.toFloat();
    float v = vStr.toFloat();

    DEBUG_SERIAL.print("ACK drive u:"); DEBUG_SERIAL.print(u);
    DEBUG_SERIAL.print(" v:");          DEBUG_SERIAL.println(v);
    mecanum_IK(u, v, 0);
    return;
  }

  // ── servo x_spd y_spd ────────────────────────────────────────────────
  if (line.startsWith("servo ")) {
    String args = line.substring(6);
    args.trim();
    int sp = args.indexOf(' ');
    if (sp < 0) { DEBUG_SERIAL.println("ERR servo format: servo x_spd y_spd"); return; }

    String xStr = args.substring(0, sp);
    String yStr = args.substring(sp + 1);
    xStr.trim(); yStr.trim();

    servoX_speed = xStr.toFloat();
    servoY_speed = yStr.toFloat();

    DEBUG_SERIAL.print("ACK servo vx:"); DEBUG_SERIAL.print(servoX_speed);
    DEBUG_SERIAL.print(" vy:");          DEBUG_SERIAL.print(servoY_speed);
    DEBUG_SERIAL.print(" | pos x:");     DEBUG_SERIAL.print(servoX_pos);
    DEBUG_SERIAL.print(" y:");           DEBUG_SERIAL.println(servoY_pos);
    return;
  }

  DEBUG_SERIAL.print("ERR unknown command: ");
  DEBUG_SERIAL.println(line);
  DEBUG_SERIAL.println("  commands: 'drive u v'  |  'servo x_spd y_spd'");
}

// ── serial reader (non-blocking) ──────────────────────────────────────────

String serialBuffer = "";

void readSerialMonitor() {
  while (DEBUG_SERIAL.available()) {
    char c = (char)DEBUG_SERIAL.read();
    if (c == '\n' || c == '\r') {
      if (serialBuffer.length() > 0) {
        handleCommand(serialBuffer);
        serialBuffer = "";
      }
    } else {
      serialBuffer += c;
    }
  }
}

// ── setup / loop ──────────────────────────────────────────────────────────

void setup() {
  DEBUG_SERIAL.begin(115200);
  DEBUG_SERIAL.println("Ready. Commands:");
  DEBUG_SERIAL.println("  drive u v       (e.g. 'drive 0.3 0')");
  DEBUG_SERIAL.println("  servo x_spd y_spd  (e.g. 'servo 30 -20')");

  servoX.attach(SERVO_X_PIN);
  servoY.attach(SERVO_Y_PIN);
  servoX.write((int)servoX_pos);
  servoY.write((int)servoY_pos);
  lastServoUpdate = millis();

  dxl.begin(1000000);
  dxl.setPortProtocolVersion(DXL_PROTOCOL_VERSION);

  uint8_t motors[4] = {DXL_ID_FL, DXL_ID_BL, DXL_ID_BR, DXL_ID_FR};
  for (int i = 0; i < 4; i++) {
    dxl.ping(motors[i]);
    dxl.torqueOff(motors[i]);
    dxl.setOperatingMode(motors[i], OP_VELOCITY);
    dxl.torqueOn(motors[i]);
  }

  delay(1000);
  DEBUG_SERIAL.println("Motors ready.");
}

void loop() {
  readSerialMonitor();
  updateServos();
}
