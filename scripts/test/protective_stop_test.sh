#!/bin/bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
UNITREE_API_PATH="${UNITREE_API_PATH:-/home/user/ws/unitree_ros2/cyclonedds_ws/src/unitree/unitree_api}"

source_ros() {
  for setup in /opt/ros/humble/setup.bash /opt/ros/jazzy/setup.bash; do
    if [ -f "$setup" ]; then
      # shellcheck disable=SC1090
      source "$setup"
      return
    fi
  done
  echo "ROS 2 setup.bash not found" >&2
  exit 1
}

build_workspace_if_needed() {
  if [ ! -f "$REPO_ROOT/install/setup.bash" ]; then
    colcon build \
      --base-paths \
        "$REPO_ROOT/estop_interfaces" \
        "$REPO_ROOT/robot_service" \
        "$REPO_ROOT/operator_client" \
        "$UNITREE_API_PATH"
  fi
}

cleanup() {
  if [ -n "${ROBOT_PID:-}" ] && kill -0 "$ROBOT_PID" 2>/dev/null; then
    kill "$ROBOT_PID" || true
    wait "$ROBOT_PID" || true
  fi
}

trap cleanup EXIT

source_ros
build_workspace_if_needed
# shellcheck disable=SC1091
source "$REPO_ROOT/install/setup.bash"

ros2 launch go2w_estop_robot robot_service.launch.py >/tmp/go2w_estop_protective_robot.log 2>&1 &
ROBOT_PID=$!
sleep 3

ros2 topic pub --once /estop/protective_stop std_msgs/msg/Empty "{}" >/dev/null
sleep 1

STATUS_OUTPUT="$(timeout 10 ros2 topic echo --once /estop/status)"
printf '%s\n' "$STATUS_OUTPUT" | grep -q "current_state: STOPPED_LATCHED"
printf '%s\n' "$STATUS_OUTPUT" | grep -q "last_trigger_type: PROTECTIVE"
printf '%s\n' "$STATUS_OUTPUT" | grep -q "latched: true"

echo "PASS: protective_stop_test"
