from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription(
        [
            DeclareLaunchArgument('rate_hz', default_value='5.0'),
            Node(
                package='ros2_pqc_demo',
                executable='raw_cmd_pub',
                name='raw_cmd_pub',
                parameters=[
                    {
                        'topic_name': '/cmd_vel/raw',
                        'rate_hz': LaunchConfiguration('rate_hz'),
                    }
                ],
                output='screen',
            ),
            Node(
                package='ros2_pqc_demo',
                executable='verified_cmd_echo',
                name='plain_cmd_echo',
                parameters=[{'topic_name': '/cmd_vel/raw'}],
                output='screen',
            ),
        ]
    )
