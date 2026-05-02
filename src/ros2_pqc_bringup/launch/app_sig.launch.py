from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    bringup_share = Path(get_package_share_directory('ros2_pqc_bringup'))

    signer_config = bringup_share / 'config' / 'signer.yaml'
    verifier_config = bringup_share / 'config' / 'verifier.yaml'

    return LaunchDescription(
        [
            DeclareLaunchArgument('keys_dir', default_value='/ros2_ws/src/keys'),
            DeclareLaunchArgument('rate_hz', default_value='5.0'),
            Node(
                package='ros2_pqc_signer',
                executable='signer_node',
                name='ros2_pqc_signer',
                parameters=[
                    str(signer_config),
                    {
                        'private_key_path': PathJoinSubstitution(
                            [LaunchConfiguration('keys_dir'), 'signer', 'mldsa44_private.key']
                        ),
                    },
                ],
                output='screen',
            ),
            Node(
                package='ros2_pqc_verifier',
                executable='verifier_node',
                name='ros2_pqc_verifier',
                parameters=[
                    str(verifier_config),
                    {
                        'trust_store_path': PathJoinSubstitution(
                            [LaunchConfiguration('keys_dir'), 'trust', 'trust_store.yaml']
                        ),
                    },
                ],
                output='screen',
            ),
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
                name='verified_cmd_echo',
                parameters=[{'topic_name': '/cmd_vel/verified'}],
                output='screen',
            ),
        ]
    )
