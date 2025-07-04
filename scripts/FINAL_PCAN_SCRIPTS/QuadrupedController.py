import rospy
import math
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

from Quadruped_config import *
from PcanController import *

class Motor:
    def __init__(self, name='no_name', id=1, min_value=0, max_value=90, offset=0, multiplier=1):
        self.name = name
        self.id = id
        self.min_value = min_value
        self.max_value = max_value
        self.offset = offset
        self.multiplier = multiplier

    def adjust_position(self, pos):
        return self.multiplier * (self.constrain(round(pos, 3)) - self.offset)
    
    def constrain(self, val):
        return max(self.min_value, min(val, self.max_value))

class QuadrupedController:
    def __init__(self):
        self.pcan_bus = PcanController()

        self.joint_positions = []
        self.motors = MOTOR_IDS

        for motor in MOTOR_IDS.keys():
            self.motors[motor] = Motor(name=motor,
                                       id=MOTOR_IDS[motor],
                                       min_value=math.radians(MOTOR_MIN_MAX_OFFSET_MULT[motor][0]),
                                       max_value=math.radians(MOTOR_MIN_MAX_OFFSET_MULT[motor][1]),
                                       offset=math.radians(MOTOR_MIN_MAX_OFFSET_MULT[motor][2]),
                                       multiplier=MOTOR_MIN_MAX_OFFSET_MULT[motor][3])

        rospy.init_node("Motor_Control_Node")
        self.joint_position_subscriber = rospy.Subscriber('/joint_group_position_controller/command', JointTrajectory, self.position_callback)
        self.pcan_bus.initialize()

        for id in MOTOR_IDS.items():
            self.pcan_bus.set_motor_origin(motor_id=id)
            self.pcan_bus.enable_motor_mode(motor_id=id)

    def position_callback(self, msg):
        self.joint_positions = msg.points[0].positions

    def run_control_loop(self):
        try:
            while True:
                for motor, position in zip(self.motors.items(),self.joint_positions):
                    feedback = self.pcan_bus.send_position(motor_id=motor.id, pos=motor.adjust_position(position))
                    print(feedback)
        
        except KeyboardInterrupt:
            print("\nDisabling motor and exiting...")
            self.pcan_bus.clean()
              