from __future__ import annotations

import math

import rclpy
from geometry_msgs.msg import Twist
from rcl_interfaces.msg import ParameterDescriptor
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy


class RawCmdPublisher(Node):
    def __init__(self) -> None:
        super().__init__('raw_cmd_pub')

        dynamic = ParameterDescriptor(dynamic_typing=True)
        self.declare_parameter('topic_name', '/cmd_vel/raw', dynamic)
        self.declare_parameter('rate_hz', 5.0, dynamic)
        self.declare_parameter('linear_x', 0.2, dynamic)
        self.declare_parameter('angular_z', 0.15, dynamic)
        self.declare_parameter('wave', True, dynamic)

        topic_name = self.get_parameter('topic_name').value
        rate_hz = max(0.1, float(self.get_parameter('rate_hz').value))

        qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )
        self._publisher = self.create_publisher(Twist, topic_name, qos)
        self._sequence = 0
        self._timer = self.create_timer(1.0 / rate_hz, self._publish)
        self.get_logger().info(f'Publishing raw Twist commands on {topic_name} at {rate_hz:.2f} Hz')

    def _publish(self) -> None:
        linear_x = float(self.get_parameter('linear_x').value)
        angular_z = float(self.get_parameter('angular_z').value)
        wave = bool(self.get_parameter('wave').value)

        msg = Twist()
        msg.linear.x = linear_x
        msg.angular.z = angular_z
        if wave:
            msg.angular.z = angular_z * math.sin(self._sequence / 5.0)

        self._publisher.publish(msg)
        self._sequence += 1


def main(args=None) -> None:
    rclpy.init(args=args)
    node = RawCmdPublisher()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
