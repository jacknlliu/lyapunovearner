import crcmod

HEADER1 = 0xAB
HEADER2 = 0xCD
CRC_PACKSTR = '<H'
CRC_SIZE = 2
crc_fun = crcmod.predefined.mkCrcFun('crc-16-usb')

MAX_JOINT_NUM = 7
COMM_TIME = 0.010

#Control mode
CTRL_MODE_TRAJ = 0x00	#Don't use it
CTRL_MODE_VEL = 0x01
CTRL_MODE_CURRENT = 0x02
CTRL_MODE_POSDYNAMICS = 0x04	#Don't use it
CTRL_MODE_TRAJDYNAMICS = 0x14
CTRL_MODE_FOLLOW = 0x05


ORDER_RUN_MODE = 0xA3
ORDER_CURRENT = 0x10
ORDER_TRAJ = 0x11
ORDER_TRAJ_VIA_CLEAR = 0x30
ORDER_TRAJ_VIA_APPEND_PT_SIN = 0x3C
ORDER_TRAJ_CTRL_START = 0x35
ORDER_SERVO_OFF = 0xA1
ORDER_SERVO_ON = 0xA2
ORDER_PARAM_KP = 0xB0
ORDER_PARAM_KI = 0xB1
ORDER_PARAM_KD = 0xB2
ORDER_RESET = 0xA0
ORDER_BRAKE_OFF = 0xC0
ORDER_BRAKE_ON = 0xC1

TRAJ_STATUS_COMPLETE = 0x04
