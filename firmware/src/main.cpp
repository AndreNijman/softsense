// Gripper controller firmware — Waveshare General Driver for Robots (ESP32-WROOM-32).
//
// Boots into a Wi-Fi access point, serves a mobile OPEN/CLOSE/calibrate web UI,
// and drives a Feetech STS bus servo (STS3250 / STS3215) plugged straight into
// the board's ST3215 bus port. Fully offline — no internet, no router.
//
//   Wi-Fi:  SSID "Gripper" / pass "gripper1234"  ->  http://192.168.4.1/
//   Servo:  Serial1 on GPIO18 (RXD) / GPIO19 (TXD), 1,000,000 baud, ID 1
//
// Power the board from ~12 V (3S) so the bus feeds the 12 V STS3250 correctly,
// and check the 3-pin connector orientation before powering up.

#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <DNSServer.h>
#include <Preferences.h>
#include <Wire.h>
#include <SCServo.h>
#include "index_html.h"

// ---- compile-time options ---------------------------------------------------
#define USE_OLED 1          // 0.91" SSD1306 on the board (set 0 to drop the dep)

// ---- board pin map (Waveshare General Driver for Robots) ---------------------
static const int S_RXD = 18;     // bus servo UART RX
static const int S_TXD = 19;     // bus servo UART TX
static const int I2C_SDA = 32;   // OLED / IMU / INA219
static const int I2C_SCL = 33;

// ---- appliance config -------------------------------------------------------
static const char *AP_SSID = "Gripper";
static const char *AP_PASS = "gripper1234";   // WPA2 needs >= 8 chars
static const uint8_t SERVO_ID = 1;            // Feetech factory default
static const uint32_t SERVO_BAUD = 1000000;
static const IPAddress AP_IP(192, 168, 4, 1);

// ---- globals ----------------------------------------------------------------
SMS_STS st;
WebServer server(80);
DNSServer dns;
Preferences prefs;

int openPos = 1024;     // placeholders — calibrate via the UI
int closePos = 3072;
int moveSpeed = 1500;   // steps/s
int moveAcc = 50;

#if USE_OLED
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
Adafruit_SSD1306 oled(128, 32, &Wire, -1);
bool hasOled = false;
#endif

// ---- config persistence (NVS) ----------------------------------------------
void loadCfg() {
  prefs.begin("gripper", true);
  openPos = prefs.getInt("open", openPos);
  closePos = prefs.getInt("close", closePos);
  moveSpeed = prefs.getInt("speed", moveSpeed);
  moveAcc = prefs.getInt("acc", moveAcc);
  prefs.end();
}
void saveCfg() {
  prefs.begin("gripper", false);
  prefs.putInt("open", openPos);
  prefs.putInt("close", closePos);
  prefs.putInt("speed", moveSpeed);
  prefs.putInt("acc", moveAcc);
  prefs.end();
}

// ---- servo ------------------------------------------------------------------
void moveTo(int pos) {
  pos = constrain(pos, 0, 4095);
  st.EnableTorque(SERVO_ID, 1);
  st.WritePosEx(SERVO_ID, pos, moveSpeed, moveAcc);
}

String statusJson() {
  String j = "{";
  int fb = st.FeedBack(SERVO_ID);          // one bus round-trip; cache the rest
  bool online = (fb != -1);
  j += "\"connected\":";
  j += online ? "true" : "false";
  if (online) {
    j += ",\"position\":" + String(st.ReadPos(-1));
    j += ",\"load\":" + String(st.ReadLoad(-1));
    j += ",\"voltage\":" + String(st.ReadVoltage(-1) / 10.0, 1);
    j += ",\"temp\":" + String(st.ReadTemper(-1));
  } else {
    j += ",\"position\":null,\"load\":null,\"voltage\":0,\"temp\":null";
  }
  j += ",\"open_pos\":" + String(openPos);
  j += ",\"close_pos\":" + String(closePos);
  j += ",\"speed\":" + String(moveSpeed);
  j += ",\"acc\":" + String(moveAcc);
  j += "}";
  return j;
}

// ---- HTTP handlers ----------------------------------------------------------
void sendJson(const String &body, int code = 200) {
  server.send(code, "application/json", body);
}
void servePage() { server.send_P(200, "text/html", INDEX_HTML); }

void handleStatus() { sendJson(statusJson()); }
void handleOpen() { moveTo(openPos); sendJson("{\"ok\":true,\"target\":" + String(openPos) + "}"); }
void handleClose() { moveTo(closePos); sendJson("{\"ok\":true,\"target\":" + String(closePos) + "}"); }

void handleGoto() {
  if (!server.hasArg("pos")) return sendJson("{\"error\":\"pos required\"}", 400);
  int p = server.arg("pos").toInt();
  moveTo(p);
  sendJson("{\"ok\":true,\"target\":" + String(constrain(p, 0, 4095)) + "}");
}

void handleTorque() {
  String v = server.arg("on");
  bool on = !(v == "0" || v == "false" || v == "off");
  st.EnableTorque(SERVO_ID, on ? 1 : 0);
  sendJson(String("{\"ok\":true,\"torque\":") + (on ? "true" : "false") + "}");
}

void handleCalibrate() {
  String which = server.arg("which");
  if (which != "open" && which != "close")
    return sendJson("{\"error\":\"which=open|close\"}", 400);
  int p = st.ReadPos(SERVO_ID);
  if (p == -1) return sendJson("{\"error\":\"servo not connected\"}", 503);
  if (which == "open") openPos = p; else closePos = p;
  saveCfg();
  sendJson("{\"ok\":true,\"" + which + "_pos\":" + String(p) + "}");
}

void handleConfig() {
  if (server.hasArg("open")) openPos = constrain(server.arg("open").toInt(), 0, 4095);
  if (server.hasArg("close")) closePos = constrain(server.arg("close").toInt(), 0, 4095);
  if (server.hasArg("speed")) moveSpeed = max(0, (int)server.arg("speed").toInt());
  if (server.hasArg("acc")) moveAcc = constrain(server.arg("acc").toInt(), 0, 255);
  saveCfg();
  sendJson(statusJson());
}

// ---- OLED -------------------------------------------------------------------
#if USE_OLED
void drawOled() {
  if (!hasOled) return;
  int pos = st.ReadPos(SERVO_ID);
  oled.clearDisplay();
  oled.setTextColor(SSD1306_WHITE);
  oled.setTextSize(1);
  oled.setCursor(0, 0);  oled.print("GRIPPER  AP");
  oled.setCursor(0, 10); oled.print(AP_SSID); oled.print("/"); oled.print(AP_PASS);
  oled.setCursor(0, 20);
  oled.print("192.168.4.1  ");
  if (pos == -1) oled.print("--"); else oled.print(pos);
  oled.display();
}
#endif

// ---- setup / loop -----------------------------------------------------------
void setup() {
  Serial.begin(115200);
  loadCfg();

  // bus servo
  Serial1.begin(SERVO_BAUD, SERIAL_8N1, S_RXD, S_TXD);
  st.pSerial = &Serial1;

#if USE_OLED
  Wire.begin(I2C_SDA, I2C_SCL);
  hasOled = oled.begin(SSD1306_SWITCHCAPVCC, 0x3C);
  if (hasOled) { oled.clearDisplay(); oled.display(); }
#endif

  // access point
  WiFi.mode(WIFI_AP);
  WiFi.softAPConfig(AP_IP, AP_IP, IPAddress(255, 255, 255, 0));
  WiFi.softAP(AP_SSID, AP_PASS);
  dns.start(53, "*", AP_IP);             // captive-portal: all names -> us

  // routes (each handles any method; UI uses POST for actions, GET for status)
  server.on("/", servePage);
  server.on("/api/status", handleStatus);
  server.on("/api/open", handleOpen);
  server.on("/api/close", handleClose);
  server.on("/api/goto", handleGoto);
  server.on("/api/torque", handleTorque);
  server.on("/api/calibrate", handleCalibrate);
  server.on("/api/config", handleConfig);
  server.onNotFound(servePage);          // captive-portal probes land on the UI
  server.begin();

  Serial.printf("Gripper AP '%s' up at %s\n", AP_SSID, AP_IP.toString().c_str());
}

void loop() {
  dns.processNextRequest();
  server.handleClient();

#if USE_OLED
  static uint32_t lastOled = 0;
  if (millis() - lastOled > 1000) { lastOled = millis(); drawOled(); }
#endif
}
