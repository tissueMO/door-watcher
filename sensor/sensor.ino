#include <ESP8266WiFi.h>
#include <WiFiClientSecure.h>
extern "C" {
  #include "user_interface.h"
}
#define CLOSE 0

// Wi-Fi 接続、通信設定
#include "settings.h"
const char* ssid = SSID;
const char* password = PASSWORD;
const char* host = HOSTNAME;
const int port = PORT;

#if PORT == 443
  WiFiClientSecure client;
#else
  WiFiClient client;
#endif

// 機器固有設定
const char* TOILET_ID = "11";

// LED I/O ピン番号
const int LED = 4;
// リードスイッチ I/O ピン番号
const int REED_SW = 5;


void setup() {
  Serial.println();
  Serial.begin(115200);
  delay(10);

  // Wi-Fi 接続
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    // 接続待ち
    delay(500);
    Serial.print(".");
  }

  // 接続成功後
  Serial.println("");
  Serial.println("Wi-Fi connected.");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());

  pinMode(REED_SW, INPUT);
}


void loop() {
  // リードスイッチの状態取得
  int door_state = digitalRead(REED_SW);

  Serial.print("Door State: ");
  if(door_state == CLOSE) {
    Serial.println("[ Close ]");
  } else {
    Serial.println("[ Open ]");
  }

  // サーバーに現在の状態を送信
  Serial.print("Connecting to ");
  Serial.println(host);
  if (!client.connect(host, port)) {
    // HTTP通信の確立に失敗
    Serial.println("Connection failed.");
    return;
  }

  // リクエスト生成
  String url;
  if(door_state == 0) {
    url += "/prod/door/close";
  } else {
    url += "/prod/door/open";
  }
  Serial.print("Requesting URL: ");
  Serial.print(host);
  Serial.println(url);

  // PUT リクエスト実行
  String body = String("{ \"toilet_id\": ") + TOILET_ID + " }";
  String request =
    String("PUT ") + url + " HTTP/1.1\r\n" +
    "Host: " + host + "\r\n" +
    "Connection: close\r\n" +
    "Content-Type: application/json\r\n" +
    "Content-Length: " + body.length() + "\r\n" +
    "\r\n" +
    body;
  Serial.println(request);
  client.print(request);
  delay(10);
  Serial.println("Closing connection.");

  // レスポンス解析
  Serial.print("Response: ");
  while(client.available()) {
    String line = client.readStringUntil('\r');
    Serial.print(line);
  }
  Serial.println();

  // リードスイッチの状態に応じて異なる待機時間で待機
  if(door_state == CLOSE) {
    //ドアが閉じている間はドアが開くまで待機
    Serial.println("DEEP SLEEP...");
    ESP.deepSleep(0, WAKE_RF_DEFAULT);
  } else {
    //ドアが開いている間はドアが閉じるまで待機
    Serial.println("DEEP SLEEP...");
    ESP.deepSleep(0, WAKE_RF_DEFAULT);
  }
  delay(1000);
}
