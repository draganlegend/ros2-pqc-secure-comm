from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription(
        [
            DeclareLaunchArgument('count', default_value='100'),
            DeclareLaunchArgument('rate_hz', default_value='20.0'),
            DeclareLaunchArgument('output_csv', default_value='/tmp/ros2_pqc_plain.csv'),
            Node(
                package='ros2_pqc_bench',
                executable='latency_runner',
                name='pqc_plain_latency_runner',
                parameters=[
                    {
                        'mode': 'plain',
                        'count': LaunchConfiguration('count'),
                        'rate_hz': LaunchConfiguration('rate_hz'),
                        'output_csv': LaunchConfiguration('output_csv'),
                    }
                ],
                output='screen',
            ),
        ]
    )
