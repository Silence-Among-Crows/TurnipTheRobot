#include <Meccanoid.h>

int chainPin = 9;
int leftMotor = 10;
int rightMotor = 11;
int duinoLight = 13;

Chain chain(chainPin);

MeccanoServo servo1 = chain.getServo(0);
MeccanoServo servo2 = chain.getServo(1);

bool servoMode = false;
bool motorMode = false;
bool fineMotorMode = false;

bool awaitingServo = false;

int selectedServo = 0;

void setup(){
  Serial.begin(9600);
  pinMode(leftMotor, OUTPUT);
  pinMode(rightMotor, OUTPUT);
  pinMode(duinoLight, OUTPUT);
  digitalWrite(duinoLight, HIGH);
}

void loop() {
  // update chain
  chain.update();
  if (servo1.justConnected()){
    servo1.setColor(0, 0, 0)
          .setPosition(90);
  }
  if (servo2.justConnected()) {
    servo2.setColor(0, 0, 0)
          .setPosition(70);
  }
  
  if (Serial.available() > 0){
    String incoming_state = Serial.readStringUntil('\n');
    Serial.println(incoming_state);
    if(incoming_state == "Clean"){
      motorMode = false;
      fineMotorMode = false;
      servoMode = false;
      awaitingServo = false;
      selectedServo = 0;
    }
    if(incoming_state == "Motor"){
      motorMode = true;
      fineMotorMode = false;
      servoMode = false;
      awaitingServo = false;
    }
    if(incoming_state == "FineMotor"){
      motorMode = false;
      fineMotorMode = true;
      servoMode = false;
      awaitingServo = false;
    }
    else if(incoming_state == "LightON"){
      digitalWrite(duinoLight, HIGH);
    }
    else if(incoming_state == "LightOFF"){
      digitalWrite(duinoLight, LOW);
    }
    else if(incoming_state == "Servo"){
      servoMode = true;
      motorMode = false;
      fineMotorMode = false;
      awaitingServo = true;
    }
    else if(servoMode == true){
      if(awaitingServo == true){
        selectedServo = incoming_state.toInt();
        awaitingServo = false;
      }
      else{
        
        executeServoMovement(incoming_state.toInt());
      }
    }
    else if (fineMotorMode == true){
      executeFineMotorMovement(incoming_state);
    }
    else if (motorMode == true){
      executeMotorMovement(incoming_state);
    }
  }
}

void executeMotorMovement(String command){
  if(command == "Stop"){
    digitalWrite(leftMotor, LOW);
    digitalWrite(rightMotor, LOW);
  }
  if(command == "Forward"){
    digitalWrite(leftMotor, HIGH);
    digitalWrite(rightMotor, HIGH);
  }
  if(command == "Left"){
    digitalWrite(leftMotor, LOW);
    digitalWrite(rightMotor, HIGH);
  }
  if(command == "Right"){
    digitalWrite(leftMotor, HIGH);
    digitalWrite(rightMotor, LOW);
  }
}

void executeFineMotorMovement(String command){
  if(command == "Left_Go"){
    digitalWrite(leftMotor, HIGH);
  }
  if(command == "Left_Stop"){
    digitalWrite(leftMotor, LOW);
  }
  if(command == "Right_Go"){
    digitalWrite(rightMotor, HIGH);
  }
  if(command == "Right_Stop"){
    digitalWrite(rightMotor, LOW);
  }
}

void executeServoMovement(int angle){
  if(selectedServo == 0){
    servo1.setPosition(angle);
  }
  else if(selectedServo == 1){
    servo2.setPosition(angle);
  }
}

