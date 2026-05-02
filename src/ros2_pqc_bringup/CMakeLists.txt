cmake_minimum_required(VERSION 3.8)
project(ros2_pqc_bringup)

find_package(ament_cmake REQUIRED)

ament_environment_hooks(
  "${CMAKE_CURRENT_SOURCE_DIR}/env-hooks/ament_prefix_path.dsv"
  "${CMAKE_CURRENT_SOURCE_DIR}/env-hooks/ament_prefix_path.sh"
)

install(DIRECTORY launch config
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
