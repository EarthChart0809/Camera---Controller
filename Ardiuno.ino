#include <Servo.h>

Servo servo_1;
Servo servo_2;
Servo servo_3;
#define SV_PIN_1  7
#define SV_PIN_2  6
#define SV_PIN_3  5

int x = 0; // aの変数
int y = 0; // bの変数
int z = 0; // cの変数

int stick[3][2]={{0}};
int botan[16]={0};
#define RMF 0
#define RMB 1
#define LMF 2
#define LMB 3
#define X 0
#define Y 1
#define A 2
#define B 3
#define LB 4
#define RB 5
#define LS 8
#define RS 9
#define LT 6
#define RT 7
#define L 0
#define R 1
#define H 2
#define BOTAN 3
#define VARTICAL 1
#define WIDTH 0
#define HAT_NUMBER 0
#define BOTAN 4
#define RIGHTMOTER_B 5
#define LEFTMOTER_B 10
#define RIGHTMOTER_F 6
#define LEFTMOTER_F 9

void setup() {
  Serial.flush();
  servo_1.attach(SV_PIN_1, 500, 2400);
  servo_2.attach(SV_PIN_2, 500, 2400);
  servo_3.attach(SV_PIN_3, 500, 2400);
  Serial.begin(115200);
  // pinMode(RIGHTMOTER_F, OUTPUT);
  // pinMode(LEFTMOTER_F, OUTPUT);
  // pinMode(RIGHTMOTER_B, OUTPUT);
  // pinMode(LEFTMOTER_B, OUTPUT);

}
int moter[4]={0};
void Serialget(){
  // 受信データがあるか確認
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n'); // 改行までの文字列を読み込む
    // 受信した文字列をカンマで分割
    int commaIndex1 = input.indexOf(',');
    int commaIndex2 = input.indexOf(',', commaIndex1 + 1);

    // 文字列からa, b, cを抽出
    if (commaIndex1 > 0 && commaIndex2 > commaIndex1) {
      String a_str = input.substring(0, commaIndex1);
      String b_str = input.substring(commaIndex1 + 1, commaIndex2);
      String c_str = input.substring(commaIndex2 + 1);

      // 文字列を整数に変換
      x = a_str.toInt();
      y = b_str.toInt();
      z = c_str.toInt();

    }
    if(x==BOTAN){
    botan[z]=y;
    Serial.println(z);
  }
  else{
    stick[x][y]=z;
    Serial.println(y);
  }
  }
}
void moterpower(int stickn,int moterf,int moterb){
  if(stick[stickn][VARTICAL]<0){
    moter[moterb]=abs(stick[stickn][VARTICAL]);
    moter[moterf]=LOW;
  }
  else{
    moter[moterf]=abs(stick[stickn][VARTICAL]);
    moter[moterb]=LOW;
  }
}
void servopower(){

}
void loop() {
  Serialget();
  moterpower(R,RMF,RMB);
  moterpower(L,LMF,LMB);
  
  analogWrite(RIGHTMOTER_F,moter[RMF]);
  delay(10);
  analogWrite(RIGHTMOTER_B,moter[RMB]);
  delay(10);
  analogWrite(LEFTMOTER_F,moter[LMF]);
  delay(10);
  analogWrite(LEFTMOTER_B,moter[LMB]);
}
