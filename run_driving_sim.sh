#!/bin/bash
# Select simulation packages even when the real workspace was sourced first.
set -eo pipefail

task_workspace=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
unset AMENT_PREFIX_PATH CMAKE_PREFIX_PATH COLCON_PREFIX_PATH PYTHONPATH LD_LIBRARY_PATH
unset COLCON_CURRENT_PREFIX AMENT_CURRENT_PREFIX
source /opt/ros/humble/setup.bash
source "$task_workspace/install/local_setup.bash"

exec ros2 launch simulation_pkg driving_sim.launch.py "$@"
