from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, EmitEvent, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    bringup_share = Path(get_package_share_directory('ros2_pqc_bringup'))
    signer_config = bringup_share / 'config' / 'signer.yaml'
    verifier_config = bringup_share / 'config' / 'verifier.yaml'
    runner = Node(
        package='ros2_pqc_bench',
        executable='latency_runner',
        name='pqc_app_sig_latency_runner',
        parameters=[
            {
                'mode': 'app_sig',
                'count': LaunchConfiguration('count'),
                'rate_hz': LaunchConfiguration('rate_hz'),
                'output_csv': LaunchConfiguration('output_csv'),
            }
        ],
        output='screen',
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument('keys_dir', default_value='/ros2_ws/src/keys'),
            DeclareLaunchArgument('count', default_value='100'),
            DeclareLaunchArgument('rate_hz', default_value='20.0'),
            DeclareLaunchArgument('output_csv', default_value='/tmp/ros2_pqc_app_sig.csv'),
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
            runner,
            RegisterEventHandler(
                OnProcessExit(
                    target_action=runner,
                    on_exit=[EmitEvent(event=Shutdown(reason='benchmark complete'))],
                )
            ),
        ]
    )
