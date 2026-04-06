# go2w_estop

Virtual emergency stop system for the Unitree GO2-W.

The system has two ROS 2 components:

- `go2w_estop_robot` runs on the Jetson and latches a Balance Stand override after a trigger.
- `go2w_estop_operator` runs on the operator PC and exposes a curses UI where `Space` sends a protective stop and `Esc` sends a hard stop.

Once triggered, the robot-side service keeps asserting Balance Stand at 5 Hz and remains latched until the robot is power-cycled.

## Repository Layout

```text
go2w_estop/
├── estop_interfaces/
├── robot_service/
├── operator_client/
├── docs/
└── scripts/test/
```

## Quickstart

Robot service in Docker:

```bash
cd robot_service
make build
make up
make logs
```

Operator client in Docker:

```bash
cd operator_client
make build
ESTOP_EXPECTED_NIC=enp97s0 make up
```

## Local Build

Deployment targets ROS 2 Humble, but the packages are also buildable on newer ROS 2 releases when the required dependencies are present.

`unitree_api` must be available in the same colcon invocation or already installed in the environment. Example:

```bash
source /opt/ros/humble/setup.bash
colcon build \
  --base-paths \
    estop_interfaces \
    robot_service \
    operator_client \
    /path/to/unitree_ros2/cyclonedds_ws/src/unitree/unitree_api
```

After building:

```bash
source install/setup.bash
ros2 launch go2w_estop_robot robot_service.launch.py
ros2 launch go2w_estop_operator operator_client.launch.py validate_nic_on_startup:=false
```

## Test Scripts

The `scripts/test` directory includes:

- `smoke_test.sh`
- `protective_stop_test.sh`
- `hard_stop_test.sh`
- `nic_validation_test.sh`

These scripts build the local workspace if needed, then exercise the main flows described in the implementation plan.
