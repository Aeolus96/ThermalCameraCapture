 #include <PRIZM.h>
 PRIZM prizm;
 int incomingByte = 0; // for incoming serial data
 void setup() {
  prizm.PrizmBegin(); // initialize the PRIZM controller
  Serial.begin(9600);
 }
 void parallelSetMotorPower(int power){
  prizm.setMotorPower(2,1.1*power); // spin Motor 2 CW at power
  prizm.setMotorPower(1,-1*power); // spin Motor 1 CW at power
 }
 void loop()
 {
  if (Serial.available() > 0) {
    // read the incoming byte:
    incomingByte = Serial.read();
    if (incomingByte == 'u'){
      parallelSetMotorPower(25);
    } else if (incomingByte == 'd'){
      parallelSetMotorPower(-25);     
    } else if (incomingByte == 'l'){
      prizm.setMotorPowers(10,10);
    } else if (incomingByte == 'r'){
      prizm.setMotorPowers(-10,-10);
    } else if (incomingByte == 's'){
      parallelSetMotorPower(0);
    }
  }
 }
