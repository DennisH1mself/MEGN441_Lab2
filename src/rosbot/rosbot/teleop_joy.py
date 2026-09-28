import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Joy

import math

class TeleopJoy(Node):
    def __init__(self):
        super().__init__('teleop_joy')
        self.publisher = self.create_publisher(Twist, '/cmd_vel', 10)
        self.subscriber = self.create_subscription(Joy, '/ros_robot_controller/joy', self.joy_callback, 10)
    def joy_callback(self, msg):
        axes = msg.axes
        buttons = msg.buttons
        cmd_vel = Twist()
        cmd_vel.linear.x = axes[3] * 0.5  # Forward/backward speed
        cmd_vel.angular.z = axes[2] * 1.0  #
        self.publisher.publish(cmd_vel)

def main(args=None):
    rclpy.init(args=args)
    node = TeleopJoy()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
if __name__ == '__main__':
    main()
