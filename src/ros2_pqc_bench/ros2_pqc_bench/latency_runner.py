from __future__ import annotations

import time
from uuid import uuid4

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from rcl_interfaces.msg import ParameterDescriptor
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy

from ros2_pqc_bench.csv_writer import BenchmarkCsvWriter
from ros2_pqc_interfaces.msg import VerificationEvent


class LatencyRunner(Node):
    def __init__(self) -> None:
        super().__init__('pqc_latency_runner')

        dynamic = ParameterDescriptor(dynamic_typing=True)
        self.declare_parameter('mode', 'app_sig', dynamic)
        self.declare_parameter('count', 100, dynamic)
        self.declare_parameter('rate_hz', 20.0, dynamic)
        self.declare_parameter('output_csv', '/tmp/ros2_pqc_benchmark.csv', dynamic)
        self.declare_parameter('raw_topic', '/cmd_vel/raw', dynamic)
        self.declare_parameter('verified_topic', '/cmd_vel/verified', dynamic)
        self.declare_parameter('event_topic', '/pqc/verify_event', dynamic)

        self._mode = str(self.get_parameter('mode').value)
        if self._mode not in ('plain', 'app_sig'):
            raise ValueError('mode must be "plain" or "app_sig"')

        self._count = max(1, int(self.get_parameter('count').value))
        self._rate_hz = max(0.1, float(self.get_parameter('rate_hz').value))
        self._raw_topic = str(self.get_parameter('raw_topic').value)
        self._verified_topic = str(self.get_parameter('verified_topic').value)
        self._event_topic = str(self.get_parameter('event_topic').value)
        self._run_id = uuid4().hex[:12]
        self._writer = BenchmarkCsvWriter(str(self.get_parameter('output_csv').value))

        qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=100,
        )

        self._publisher = self.create_publisher(Twist, self._raw_topic, qos)
        self._sent_perf_ns: dict[int, int] = {}
        self._published = 0
        self._recorded = 0
        self.done = False

        if self._mode == 'plain':
            self._plain_sub = self.create_subscription(Twist, self._raw_topic, self._on_plain_echo, qos)
        else:
            self._event_sub = self.create_subscription(
                VerificationEvent,
                self._event_topic,
                self._on_verify_event,
                qos,
            )

        self._timer = self.create_timer(1.0 / self._rate_hz, self._publish_one)
        self.get_logger().info(
            f'Benchmark started: mode={self._mode}, count={self._count}, output={self._writer.output_path}'
        )

    def _publish_one(self) -> None:
        if self._published >= self._count:
            self._timer.cancel()
            return

        sequence = self._published
        msg = Twist()
        msg.linear.x = float(sequence)
        msg.angular.z = 0.1

        self._sent_perf_ns[sequence] = time.perf_counter_ns()
        self._publisher.publish(msg)
        self._published += 1

    def _on_plain_echo(self, msg: Twist) -> None:
        sequence = int(msg.linear.x)
        if sequence < 0 or sequence >= self._count:
            return
        if sequence not in self._sent_perf_ns:
            return

        e2e_ns = time.perf_counter_ns() - self._sent_perf_ns.pop(sequence)
        self._write_result(
            sequence=sequence,
            sign_ns=0,
            verify_ns=0,
            age_ns=0,
            e2e_ns=e2e_ns,
            result_code=0,
        )

    def _on_verify_event(self, msg: VerificationEvent) -> None:
        sequence = int(msg.sequence)
        sent_ns = self._sent_perf_ns.pop(sequence, None)
        if sent_ns is None:
            return

        # SignedTwist does not carry signer processing duration in v1, so the
        # benchmark keeps the required CSV column and records 0 for sign_ns.
        self._write_result(
            sequence=sequence,
            sign_ns=0,
            verify_ns=int(msg.verify_ns),
            age_ns=int(msg.age_ns),
            e2e_ns=int(msg.age_ns) if msg.ok else 0,
            result_code=int(msg.result_code),
        )

    def _write_result(
        self,
        *,
        sequence: int,
        sign_ns: int,
        verify_ns: int,
        age_ns: int,
        e2e_ns: int,
        result_code: int,
    ) -> None:
        self._writer.write_row(
            {
                'run_id': self._run_id,
                'mode': self._mode,
                'sequence': sequence,
                'sign_ns': sign_ns,
                'verify_ns': verify_ns,
                'age_ns': age_ns,
                'e2e_ns': e2e_ns,
                'result_code': result_code,
            }
        )
        self._recorded += 1
        if self._recorded >= self._count:
            self.done = True
            self._writer.close()
            self.get_logger().info(f'Benchmark complete: {self._writer.output_path}')


def main(args=None) -> None:
    rclpy.init(args=args)
    node = LatencyRunner()
    try:
        while rclpy.ok() and not node.done:
            rclpy.spin_once(node, timeout_sec=0.1)
    finally:
        if not node.done:
            node._writer.close()
        node.destroy_node()
        rclpy.shutdown()
