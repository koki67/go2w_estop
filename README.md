# go2w_estop

Virtual emergency stop system for the Unitree GO2-W.

Experimental software-only project. Not a certified safety system and not a substitute for a physical emergency stop.

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
├── third_party/
├── docs/
└── scripts/test/
```

## Clone

The repository vendors its ROS 2 message dependency as a git submodule:

```bash
git clone --recurse-submodules https://github.com/koki67/go2w_estop.git
```

If you already cloned without submodules:

```bash
git submodule update --init --recursive
```

## Quickstart

On the robot hardware, start the robot-side service:

```bash
cd robot_service
make build
make up
make logs
```

`make up` starts the robot service in the background. `make logs` is optional, but useful to confirm it is alive and publishing status.

On the operator PC, start the operator client:

```bash
cd operator_client
make build
ESTOP_EXPECTED_NIC=enp97s0 make up
```

`make up` for the operator client stays attached and opens the curses UI in that same terminal. That operator-side terminal is where `Space`, `Esc`, and `q` are read.

## How To Use It

Starting the services does not trigger a stop by itself. The stop command is only sent after the operator UI is visible on the operator PC and you press a key there.

Recommended runtime flow:

1. On the robot hardware, start `go2w_estop_robot`.
2. On the operator PC, start `go2w_estop_operator`.
3. Wait for the operator UI to appear and confirm:
   - `Connection         : CONNECTED`
   - `Current state      : READY`
4. Press `Space` in the operator UI for a protective stop.
5. Press `Esc` in the operator UI for a hard stop.

What each key does:

- `Space` publishes a protective stop.
- `Esc` publishes a hard stop.
- `q` quits the operator client only. It does not clear a latched stop.

What happens after a trigger:

- The robot-side service latches the stop and keeps asserting Balance Stand at 5 Hz.
- The latched stop remains active until the robot is power-cycled.

If the operator UI does not appear, the most likely cause is NIC validation failure. By default the operator client expects `enp97s0`.

## Local Build

Deployment targets ROS 2 Humble, but the packages are also buildable on newer ROS 2 releases when the required dependencies are present.

`unitree_api` is provided by the pinned submodule at `third_party/unitree_ros2`. Example:

```bash
source /opt/ros/humble/setup.bash
git submodule update --init --recursive
colcon build \
  --base-paths \
    estop_interfaces \
    robot_service \
    operator_client \
    third_party/unitree_ros2/cyclonedds_ws/src/unitree/unitree_api
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

## Licensing

This repository's own code is released under the BSD 3-Clause license in [`LICENSE`](LICENSE).

The `third_party/unitree_ros2` directory is a separate git submodule that preserves its own upstream license and history. See [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) and the submodule's own `LICENSE` file for details.
