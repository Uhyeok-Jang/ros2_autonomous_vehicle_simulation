import math

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile
from rclpy.qos import QoSHistoryPolicy
from rclpy.qos import QoSDurabilityPolicy
from rclpy.qos import QoSReliabilityPolicy
from std_msgs.msg import String
from geometry_msgs.msg import Twist
from interfaces_pkg.msg import MotionCommand


#------------- config.py에서 수정 권장 ------------
from simulation_pkg.config import SimulationSenderSettings as set
#from simulation_pkg.config import control_motor as CONTROL
#from simulation_pkg.config import convert_arduino_msg as PROTOCOL

SUB_TOPIC_NAME = set.MOTION_PLANNER_TOPIC 
PUB_TOPIC_NAME = set.GAZEBO_CONTROL_TOPIC

STEER = set.STEERING
DIRECT = set.DIRECTION

MAX_SPEED = set.MAX_SPEED
# ----------------------------------------------


class SendSignal():
  def __init__(self):
    pass
  
  def map_to_steer(self, input_value):
    """Map integer steering command to a progressive wheel angle.

    MotionCommand.steering is int32 in the course interface, so a linear
    -7..7 mapping makes the smallest non-zero command already about 0.092 rad
    (5.3 deg) when max_steer=0.6458 rad. That is too coarse around center and
    causes abrupt turn-in/corner cutting. A quadratic response keeps the same
    maximum steering angle while giving much finer low-angle control.
    """
    max_steer = 0.6458  # 최대 바퀴 조향각 (rad)
    input_min = -7.0
    input_max = 7.0

    clipped = max(input_min, min(input_max, float(input_value)))
    normalized = clipped / input_max  # -1.0 ~ 1.0

    # Progressive response:
    # command 1 -> ~0.013 rad (0.76 deg)
    # command 2 -> ~0.053 rad (3.0 deg)
    # command 3 -> ~0.119 rad (6.8 deg)
    # command 7 ->  0.646 rad (37.0 deg)
    wheel_angle = math.copysign(
        max_steer * (abs(normalized) ** 2),
        normalized
    ) if normalized != 0.0 else 0.0

    return wheel_angle
  
  def map_to_speed(self, input_speed):      
      max_speed = MAX_SPEED
      input_min = -255
      input_max = 255

      # 좌측 바퀴 속도 변환
      normalized_input_speed = (input_speed - input_min) / (input_max - input_min) * 2 - 1
      mapped_input_speed = normalized_input_speed * max_speed

      return mapped_input_speed
      
  def map_to_twist(self, steer, left, right):
    max_speed = MAX_SPEED
      
    normalized_left_speed = (left / 255.0) * max_speed
    normalized_right_speed = (right / 255.0) * max_speed
      
    # 두 속도의 평균을 통해 전진 속도 계산
    speed_x = (normalized_left_speed + normalized_right_speed) / 2.0
    
    # 차량의 축간 거리와 Ackermann 조향 시스템을 고려하여 각속도 계산
    wheel_base = 2.86
    
    # 조향각에 따른 각속도 계산 (Ackermann 조향 모델 사용)
    if steer != 0:
        radius = wheel_base / abs(steer)  # 회전 반경
        steer_z = speed_x / radius        # 각속도는 속도를 반경으로 나눈 값
    else:
        steer_z = 0.0  # 조향각이 0이면 각속도는 0
    
    return speed_x, steer_z


  def process(self, motor):
    steer = self.map_to_steer(STEER * motor.steering)
    
    left_speed = self.map_to_speed(DIRECT * motor.left_speed)
    right_speed = self.map_to_speed(DIRECT * motor.right_speed)
  
    return steer, left_speed, right_speed

class MotorControlNode(Node):
  def __init__(self, sub_topic=SUB_TOPIC_NAME, pub_topic=PUB_TOPIC_NAME):
    super().__init__('simulation_sender_node')
    
    self.declare_parameter('sub_topic', sub_topic)
    self.declare_parameter('pub_topic', pub_topic)
    
    self.sub_topic = self.get_parameter('sub_topic').get_parameter_value().string_value
    self.pub_topic = self.get_parameter('pub_topic').get_parameter_value().string_value
    qos_profile = QoSProfile(reliability=QoSReliabilityPolicy.RELIABLE, history=QoSHistoryPolicy.KEEP_LAST, durability=QoSDurabilityPolicy.VOLATILE, depth=1)
    
    self.simul = SendSignal()
    self.subscription = self.create_subscription(MotionCommand, self.sub_topic, self.data_callback, qos_profile)
    
    self.publisher = self.create_publisher(Twist, self.pub_topic, qos_profile)
    self.timer = self.create_timer(0.1, self.send_cmd_vel)
    self.velocity = Twist()
    
  def send_cmd_vel(self):
    self.publisher.publish(self.velocity)

  def data_callback(self, motor):
    angle, left, right = self.simul.process(motor)
        
    self.velocity.angular.z = float(angle)
    self.velocity.linear.x = float(left)
  
    self.publisher.publish(self.velocity)
    
  def stop_cmd(self):
    self.velocity.linear.x = 0.0
    
    self.publisher.publish(self.velocity)
    self.get_logger().error("\n\nRobot stopped\n\n")
    
def main(args=None):
  rclpy.init(args=args)
  node = MotorControlNode()
  try:
    rclpy.spin(node)
  except KeyboardInterrupt:
    node.stop_cmd()
    node.get_logger().fatal("\n\nsimulation_sender_node shutdown!!!\n\n")
  finally:
    node.destroy_node()
    rclpy.shutdown()
  
if __name__ == '__main__':
  main()
