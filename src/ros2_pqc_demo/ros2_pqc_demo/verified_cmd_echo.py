from __future__ import annotations

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy


class VerifiedCmdEcho(Node):
    def __init__(self) -> None:
        super().__init__('verified_cmd_echo')

        self.declare_parameter('topic_name', '/cmd_vel/verified')
        topic_name = self.get_parameter('topic_name').value

        qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )
        self._subscription = self.create_subscription(Twist, topic_name, self._on_twist, qos)
        self._count = 0
        self.get_logger().info(f'Echoing verified Twist commands from {topic_name}')

    def _on_twist(self, msg: Twist) -> None:
        self._count += 1
        self.get_logger().info(
            'verified[%d] linear=(%.3f, %.3f, %.3f) angular=(%.3f, %.3f, %.3f)'
            % (
                self._count,
                msg.linear.x,
                msg.linear.y,
                msg.linear.z,
                msg.angular.x,
                msg.angular.y,
                msg.angular.z,
            )
        )


def main(args=None) -> None:
    rclpy.init(args=args)
    node = VerifiedCmdEcho()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
