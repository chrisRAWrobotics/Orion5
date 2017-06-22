#include "G15.h"
#include "TorqueConstants.h"

#define NUM_SERVOS 5
#define USB_BAUD_RATE 250000
#define G15_BAUD_RATE 250000
#define USB Serial
#define LED_PIN 11
#define DEG2RAD 0.0174533
#define POS2RADS 0.00577498649

//Limit Macros
#define SHOULDERMIN 20
#define SHOULDERMAX 359
//map(var, 45, 160, 359, 20);
#define SHOULDERGEARINGMIN 45
#define SHOULDERGEARINGMAX 160
#define ELBOWMIN 20
#define ELBOWMAX 320
#define WRISTMIN 80
#define WRISTMAX 280
#define CLAWMIN 120
#define CLAWMAX 300

typedef enum {BASE, SHOULDER, ELBOW, WRIST, CLAW} joint_name;
typedef enum {CW_LIMIT, CCW_LIMIT, MARGIN, SLOPE, PUNCH, TORQUE_EN, GOAL_POS, SERVO_SPEED, MODE, CURRENT_POS, CURRENT_SPEED, CURRENT_LOAD, CHECKER} var_name;

G15 allServos(254);
G15 servos[] = {G15(1), G15(2), G15(3), G15(4), G15(5)};
int16_t goal_angles[NUM_SERVOS];
int16_t angles[NUM_SERVOS];
int16_t goal_angles_rg[NUM_SERVOS];
int16_t angles_rg[NUM_SERVOS];
uint8_t servo_index = 0;
uint8_t checker = 0;

// shoulder, elbow, wrist, payload
int8_t dirs[3];
int16_t joint_torques[] = {0, 0, 0};

// buffers
uint8_t read_buffer[2];
uint8_t send_buffer[10];
uint8_t var_buffer[4];

int16_t wrapTo360(int16_t angle) {
  angle = angle % 360;
  if (angle < 0) {
    angle += 360;
  }
  return angle;
}

int16_t wrapTo180(int16_t angle) {
  angle = (angle + 180) % 360;
  if (angle < 0) {
    angle += 360;
  }
  return (angle - 180);
}
  
void buildSendPacket(byte* buff, uint8_t Packet_type, uint8_t checkerPacket, uint8_t jointID, uint8_t error, uint16_t speed12_t, uint16_t load12_t, uint16_t position12_t) {  
  // <0000 0000> = 1 byte
  // <Packet_type errorID> <Checker>
  // <Packet_type errorID> <JointID VarH> <VarM VarL>
  // <Packet_type errorID> <jointID speedH> <speedM speedL> <loadH loadM> <loadL posH> <posM posL>
  buff[0] = 0xF0;
  buff[1] = 0xF0;
  if (Packet_type == 0) {
    buff[2] = (((Packet_type & 0x000F) << 4) | (error & 0x000F));
    buff[3] = (((jointID & 0x000F) << 4) | ((speed12_t & 0x0F00) >> 8)); //jointID is 4bit otherwise it loses information
    buff[4] = (speed12_t & 0x00FF);
    buff[5] = ((load12_t & 0x0FF0) >> 4);
    buff[6] = (((position12_t & 0x0F00) >> 8) | ((load12_t & 0x000F) << 4)); //keeping the top 4 bits of the 12bit data in the 16bit integer, shifting it down to the base of the 8bit range
    buff[7] = (position12_t & 0x00FF); //keeping the 8bits of the 16bit number, discarding the rest*/
    buff[8] = 0xE0;
    buff[9] = 0xE0;
  } else if (Packet_type == 1) {
    buff[2] = (((Packet_type & 0x000F) << 4) | (error & 0x000F));
    buff[3] = checkerPacket;
    buff[4] = 0xE0;
    buff[5] = 0xE0;
  } else {
    buff[2] = (((Packet_type & 0x000F) << 4) | (error & 0x000F));
    buff[3] = (((jointID & 0x000F) << 4) | ((position12_t & 0x0F00) >> 8)); //jointID is 4bit otherwise it loses information
    buff[4] = (position12_t & 0x00FF);
    buff[5] = 0xE0;
    buff[6] = 0xE0;
  }
}

void getNextServoAngle() {
  // cycle through servos updating all structs (nek revision)
  servos[servo_index].GetPos((byte*) read_buffer);
  angles[servo_index] = ((read_buffer[1] & 0x03) << 8) | read_buffer[0];
  angles[servo_index] = ConvertPos2Angle(angles[servo_index]);
  if (servo_index == SHOULDER) {
    angles[servo_index] = map(angles[servo_index], SHOULDERMIN, SHOULDERMAX, SHOULDERGEARINGMAX, SHOULDERGEARINGMIN);
  } else if (servo_index == WRIST) {
    angles[servo_index] = 360 - angles[servo_index];
  }

  switch(servo_index) {
    case SHOULDER:
      angles_rg[SHOULDER] = angles[SHOULDER];
      goal_angles_rg[SHOULDER] = goal_angles[SHOULDER];
    case ELBOW:
      angles_rg[ELBOW] = wrapTo360(angles[SHOULDER] + angles[ELBOW] - 180);
      goal_angles_rg[ELBOW] = wrapTo360(goal_angles[SHOULDER] + goal_angles[ELBOW] - 180);
    break;
    case WRIST:
      angles_rg[WRIST] = wrapTo360(angles[SHOULDER] + angles[ELBOW] + angles[WRIST]);
      goal_angles_rg[WRIST] = wrapTo360(goal_angles[SHOULDER] + goal_angles[ELBOW] + goal_angles[WRIST]);
    break;
  }
  
  // increment and wrap servo index
  if (++servo_index >= NUM_SERVOS) {
    servo_index = 0;
  }
}

void setup() {
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH);
  
  // USB SERIAL INIT
  USB.begin(USB_BAUD_RATE);
  while (!USB.dtr());
  digitalWrite(LED_PIN, LOW);
  
  // INITIALISE SERVOS WITH SETTINGS
  G15ShieldInit(G15_BAUD_RATE, 3, 8);
  allServos.init();
  for(int i=0; i<NUM_SERVOS; ++i) {
    servos[i].init();
    servos[i].SetTemperatureLimit(80);
    servos[i].SetMarginSlopePunch(0, 0, 100, 100, 40);
    servos[i].SetAngleLimit(0, 1087);
    servos[i].SetLED(1, iWRITE_DATA);
    getNextServoAngle();
    goal_angles[i] = angles[i];
  }
  
  // SET JOINT LIMITS
  servos[SHOULDER].SetAngleLimit(ConvertAngle2Pos(SHOULDERMIN), ConvertAngle2Pos(SHOULDERMAX));
  servos[ELBOW].SetAngleLimit(ConvertAngle2Pos(ELBOWMIN), ConvertAngle2Pos(ELBOWMAX));
  servos[WRIST].SetAngleLimit(ConvertAngle2Pos(WRISTMIN), ConvertAngle2Pos(WRISTMAX));
  servos[CLAW].SetAngleLimit(ConvertAngle2Pos(CLAWMIN), ConvertAngle2Pos(CLAWMAX));
  
  // ALL LEDs OFF MEANS INIT FINISHED
  allServos.SetLED(0, iWRITE_DATA);
  delay(100);
}

void loop() {
  getNextServoAngle();
  
  uint16_t tempContainers[] = {0, 0, 0};
  tempContainers[0] = SlopePosWrist[angles_rg[WRIST]];
  tempContainers[1] = SlopeNegWrist[angles_rg[WRIST]];
  tempContainers[2] = PunchWrist[angles_rg[WRIST]];
  servos[WRIST].SetMarginSlopePunch(0, 0, tempContainers[0], tempContainers[1], tempContainers[2]);

  tempContainers[0] += SlopePosElbow[angles_rg[ELBOW]];
  tempContainers[1] += SlopeNegElbow[angles_rg[ELBOW]];
  tempContainers[2] += PunchElbow[angles_rg[ELBOW]];
  servos[ELBOW].SetMarginSlopePunch(0, 0, tempContainers[0], tempContainers[1], tempContainers[2]);

  tempContainers[0] += SlopePosShoulder[angles_rg[SHOULDER]];
  tempContainers[1] += SlopeNegShoulder[angles_rg[SHOULDER]];
  tempContainers[2] += PunchShoulder[angles_rg[SHOULDER]];
  servos[SHOULDER].SetMarginSlopePunch(0, 0, tempContainers[0], tempContainers[1], tempContainers[2]);

  // check if anything in serial buffer
  if (USB.available() > 5) {
    digitalWrite(LED_PIN, HIGH);
    uint8_t firstByte[1] = {0};
    uint8_t secondByte[1] = {0};
    while (USB.available() > 5) {
      USB.readBytes((char*)firstByte, 1);
      //firstByte = USB.read();
      if (firstByte[0] == 240) {
        USB.readBytes((char*)secondByte, 1);
        //secondByte = USB.read();
        if (secondByte[0] == 240) {
          break;  
        }
      }
    }
    
    if ((firstByte[0] == 240) && (secondByte[0] == 240)) {    
      // a variable update
      // unpack the jointID, varID, value
      USB.readBytes((char*)var_buffer, 4);
      uint16_t var = (var_buffer[1] << 8) | var_buffer[2];
      //var = (var << 8) | var_buffer[2];
      checker = var_buffer[3];
      uint8_t jointIndex = ((var_buffer[0] & 0xF0) >> 4) - 1;
      uint8_t varID = (var_buffer[0] & 0x0F);
  
      // apply the variable update
      switch (varID) {
        case(GOAL_POS):
          switch (jointIndex) {
            case SHOULDER:
                var = map(var, SHOULDERGEARINGMIN, SHOULDERGEARINGMAX, SHOULDERMAX, SHOULDERMIN); // map(var, 45, 160, 359, 20);
                break;
            case WRIST:
                var = 360 - var;
                break;
          }
          servos[jointIndex].SetPos(ConvertAngle2Pos(var), iWRITE_DATA);
          goal_angles[jointIndex] = var;
          break;
        case (SERVO_SPEED):
          if (var < 1) var = 1;
          servos[jointIndex].SetTimetoGoal(var, iWRITE_DATA);
          break;
        case (TORQUE_EN):
          servos[jointIndex].SetTorqueOnOff(var, iWRITE_DATA);
          break;
        case (CHECKER):
          // request for joint angles
          for (uint8_t i=0; i<NUM_SERVOS; ++i) {
            buildSendPacket(send_buffer, 0, checker, i+1, 0, 0, 0, angles[i]);
            //buildSendPacket(send_buffer, i+1, angles[i]);
            USB.write(send_buffer, 10);
          }
          break;
      }  
    }
  }
    
  //send the Checker
  buildSendPacket(send_buffer, 1, checker, 0, 0, 0, 0, 0);
  USB.write(send_buffer, 6);
  digitalWrite(LED_PIN, LOW);
}

