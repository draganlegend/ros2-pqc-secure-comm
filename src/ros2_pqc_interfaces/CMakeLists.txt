cmake_minimum_required(VERSION 3.8)
project(ros2_pqc_interfaces)

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(builtin_interfaces REQUIRED)

ament_environment_hooks(
  "${CMAKE_CURRENT_SOURCE_DIR}/env-hooks/ament_prefix_path.dsv"
  "${CMAKE_CURRENT_SOURCE_DIR}/env-hooks/ament_prefix_path.sh"
)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/SignedTwist.msg"
  "msg/VerificationEvent.msg"
  DEPENDENCIES std_msgs geometry_msgs builtin_interfaces
)

ament_export_dependencies(rosidl_default_runtime)

ament_package()
