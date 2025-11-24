#include <WiFi.h>
#include <ArduinoOSCWiFi.h>
#include "DFRobot_MCP9808.h"
#include <WiFiManager.h> // by tzapu
#include <Preferences.h>

#define I2C_ADDRESS  MCP9808_ADDRESS_7
DFRobot_MCP9808_I2C mcp9808(&Wire, I2C_ADDRESS);

WiFiManager wm;
Preferences preferences;

WiFiManagerParameter custom_ip("osc_ip", "OSC Target IP", "", 16);
WiFiManagerParameter custom_port("osc_port", "OSC Port", "8000", 6);

String destIp;
int destPort;

// part of an old code for manually adding wifi network
//const char* ssid     = "vrouwenvolk2.4G";
//const char* password = "AbFabForever";
//const char* destIp   = "10.2.1.78";
//const int destPort   = 8000;


// Wearable sensor data
float p1s1; //Person 1, sensor 1 // change accordingly
float trigger;
float prevTemp = 0;
float highestTemp = 32;
float lowestTemp = 29;
int count;


//calibration vals

const int numReadings = 10;
int readings[numReadings];
float Baseline0_1 = 0;
float Threshold2;
float total;
float ValTemp;


void setup() {
  Serial.begin(115200);
  pinMode(LED_RED, OUTPUT);
  pinMode(LED_GREEN, OUTPUT);
  pinMode(LED_BLUE, OUTPUT);
  pinMode(LED_BUILTIN, OUTPUT);
  // Initialize MCP9808 Sensor
  while (!mcp9808.begin()) {
    Serial.println("Temp Sensor Begin Failed! Retrying...");
    delay(1000);
  }
  Serial.println("Temperature Sensor Initialized!");

  if (!mcp9808.wakeUpMode()) {
    Serial.println("Sensor Locked! Unlock Required.");
  } else {
    Serial.println("Sensor Awake, Ready for Readings.");
  }

  if (mcp9808.setResolution(RESOLUTION_0_0625)) {
    Serial.println("Temperature Resolution Set Successfully!");
  } else {
    Serial.println("Resolution Setting Failed!");
  }
  
// part of an old code for manually adding wifi network
////   Initialize WiFi
//  WiFi.begin(ssid, password);
//  while (WiFi.status() != WL_CONNECTED) {
//    delay(500);
//    Serial.print(".");
//  }
//  Serial.println("\nWiFi Connected!");

// Add custom parameters before autoConnect
  WiFiManager wm;
  wm.addParameter(&custom_ip);
  wm.addParameter(&custom_port);

  bool res = wm.autoConnect("ESP32_AP");

  if (!res) {
    Serial.println("Failed to connect — rebooting");
    ESP.restart();
  }

  // ALWAYS check after portal or autoConnect
  if (strlen(custom_ip.getValue()) > 0) {
    preferences.begin("osc_settings", false);
    preferences.putString("ip", custom_ip.getValue());
    preferences.putString("port", custom_port.getValue());
    preferences.end();

    Serial.println("User entered IP & Port, saved:");
    Serial.println(custom_ip.getValue());
    Serial.println(custom_port.getValue());
  } else {
    Serial.println("No new parameters entered — using saved values");
  }

  // Now load for OSC usage
  preferences.begin("osc_settings", true);
  destIp = preferences.getString("ip", "");
  destPort = preferences.getString("port", "8000").toInt();
  preferences.end();

  Serial.print("Loaded OSC IP: ");
  Serial.println(destIp);
  Serial.print("Loaded OSC Port: ");
  Serial.println(destPort);

  if (destIp == "") {
    Serial.println("No OSC IP saved — restarting to force config");
    delay(3000);
    wm.resetSettings();  // Optional: clear WiFi and force portal next time
    ESP.restart();
  }

//  // Place this temporarily in setup(), run once, then remove it:
//resets all wifi settings from wifi manager
//wm.resetSettings();
//
//preferences.begin("osc_settings", false);
//preferences.clear();
//preferences.end();
//
//Serial.println("Settings cleared — rebooting...");
//delay(2000);
//ESP.restart();
//

  Serial.println("WiFi connected");
  Serial.print("OSC IP: ");
  Serial.println(destIp);
  Serial.print("OSC Port: ");
  Serial.println(destPort);

float Baseline0_1 = 0;

  digitalWrite(LED_BUILTIN, HIGH);   
  digitalWrite(LED_RED, LOW);
  digitalWrite(LED_GREEN, HIGH);
  digitalWrite(LED_BLUE, HIGH);
  delay(100);                      
  digitalWrite(LED_BUILTIN, LOW);    
  delay(100);                      
  digitalWrite(LED_BUILTIN, HIGH);   
  delay(100);                       
  digitalWrite(LED_BUILTIN, LOW);   
  delay(100);                      
  digitalWrite(LED_BUILTIN, HIGH); 
  digitalWrite(LED_BUILTIN, LOW);   
  digitalWrite(LED_BLUE, LOW); 
  digitalWrite(LED_RED, HIGH); 
  delay(3000); 
  digitalWrite(LED_BLUE, HIGH); 
  digitalWrite(LED_GREEN, LOW);
  delay (100);
  digitalWrite(LED_GREEN, HIGH);
}

void loop() {
  // Read Temperature
  p1s1 = mcp9808.getTemperature();
  int scaledValLED = map(p1s1, Baseline0_1, Threshold2, 0, 255);  // scale to 0-255

  int redValue = 255 - scaledValLED;
  int blueValue = scaledValLED;
  analogWrite(LED_RED, redValue);
  analogWrite(LED_BLUE, blueValue);


if (Baseline0_1 == 0){
  calibration();
  Serial.println("start new calibration");  
}
  
  
  if (p1s1 > highestTemp) {
    Serial.println("!Getting hotter than ever before!");
    trigger = 1;
    OscWiFi.send(destIp, destPort, "/trigger/wearableA", trigger); //triggers based on data
  } else if (p1s1 < lowestTemp) {
    Serial.println("phew.. we are cooling  down");
    trigger = 2;
    OscWiFi.send(destIp, destPort, "/trigger/wearableA", trigger); //triggers based on data
  } else {
    Serial.println("keep going..");
    trigger = 0;
    OscWiFi.send(destIp, destPort, "/trigger/wearableA", trigger); //triggers based on data
  }

  if (p1s1 != prevTemp && p1s1 != 0) { //if p1 is not equal to prevtemp and not equal to 0, we sent the data and reset prevtemp values
    OscWiFi.send(destIp, destPort, "/arduino1/sensordata", p1s1); //Wearable 1, Person 1, sensor 1 // change accordingly
    prevTemp = p1s1;
    count = 0;
    trigger = 0;
    OscWiFi.send(destIp, destPort, "/trigger/wearableA", trigger); //triggers based on data
    OscWiFi.send(destIp, destPort, "/arduino1/Baseline0_1", Baseline0_1); //triggers based on data
    Serial.println(p1s1);
  } else if (p1s1 == prevTemp || p1s1 == 0) { // if p1 is equal to prevtemp or 0, we count how long, and sent a trigger if change is not happening
    count++;
    Serial.println("no change or 0");
    if (count >= 20) {
      trigger = 3;
      count = 0;
      OscWiFi.send(destIp, destPort, "/trigger/wearableA", trigger); //triggers based on data
    }
  }

if (p1s1 <= (Baseline0_1 - 6)){
  Serial.println("too low New calibration needed");
  delay(3000);
  calibration();
}

  // Send Data via OSC
  //    OscWiFi.send(destIp, destPort, "/arduino2/sensordata", p2s1, p2s2); // This is if one wearable would have multiple sensors
  //     OscWiFi.send(destIp, destPort, "/trigger/wearableA", trigger); //triggers based on data

  delay(500);  // Sending data
}

void calibration(){
  // Compute baseline
  total= 0.0;
  for (int i = 0; i < numReadings; i++) {
     ValTemp = mcp9808.getTemperature();
    total += ValTemp;
    readings[i] = ValTemp;
    delay(10);
  }
  Baseline0_1 = total / numReadings;
  Threshold2 = Baseline0_1 + 3; // Dynamic threshold initialization
  Serial.print("Baseline: ");
  Serial.println(Baseline0_1);
  Serial.print("Initial Threshold: ");
  Serial.println(Threshold2);

   OscWiFi.send(destIp, destPort, "/arduino1/Baseline0_1", Baseline0_1); //triggers based on data
}
