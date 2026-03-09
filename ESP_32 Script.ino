#include <WiFi.h>
#include <WebSocketsServer.h>

#define WIFI_SSID "hiteshi"
#define WIFI_PASSWORD "21022005"

/******** STATIC IP ********/

IPAddress local_IP(10,137,252,50);
IPAddress gateway(10,137,252,168);
IPAddress subnet(255,255,255,0);

WebSocketsServer webSocket = WebSocketsServer(81);

bool sampling=false;
unsigned long lastSample=0;

const int SAMPLE_INTERVAL=10;


void webSocketEvent(uint8_t num,
                    WStype_t type,
                    uint8_t * payload,
                    size_t length)
{

  if(type==WStype_CONNECTED)
  Serial.println("Client Connected");


  if(type==WStype_TEXT)
  {

    String msg=(char*)payload;

    if(msg=="START")
    {
      sampling=true;
      Serial.println("START");
    }

    if(msg=="STOP")
    {
      sampling=false;
      Serial.println("STOP");
    }

  }

}



void setup()
{

Serial.begin(115200);

WiFi.config(local_IP,gateway,subnet);

WiFi.begin(WIFI_SSID,WIFI_PASSWORD);

Serial.print("Connecting");

while(WiFi.status()!=WL_CONNECTED)
{
delay(500);
Serial.print(".");
}

Serial.println();

Serial.print("ESP IP Address: ");
Serial.println(WiFi.localIP());

webSocket.begin();
webSocket.onEvent(webSocketEvent);

}



void loop()
{

webSocket.loop();

unsigned long now=millis();

if(sampling && now-lastSample>=SAMPLE_INTERVAL)
{

lastSample=now;

int h2o=analogRead(34);
int co2=analogRead(35);
int co=analogRead(32);

char msg[50];

sprintf(msg,"%d,%d,%d",h2o,co2,co);

webSocket.broadcastTXT(msg);

}

}
