# GO2-W Virtual Emergency Stop System

This document is the checked-in specification used to implement the repository.

## Overview

The system provides a software-only virtual emergency stop for the Unitree GO2-W:

- The operator presses `Space` or `Esc` in a terminal client.
- The robot-side service receives the trigger over ROS 2.
- The robot-side service publishes Balance Stand (`api_id=1002`) to `/api/sport/request` at 5 Hz.
- The stop is latched in software and remains active until a physical power-cycle.

The repository contains three ROS 2 packages:

- `estop_interfaces`
- `go2w_estop_robot`
- `go2w_estop_operator`

## Topics

| Topic | Type | Publisher | Subscriber |
|---|---|---|---|
| `/estop/protective_stop` | `std_msgs/msg/Empty` | operator | robot |
| `/estop/hard_stop` | `std_msgs/msg/Empty` | operator | robot |
| `/estop/status` | `estop_interfaces/msg/EstopStatus` | robot | operator |
| `/api/sport/request` | `unitree_api/msg/Request` | robot | robot main board |

## Robot-Side Behavior

- Subscribes to protective and hard stop trigger topics.
- Publishes status continuously at 2 Hz.
- On first trigger, enters a stopping state.
- On the first 5 Hz assertion tick after trigger receipt, transitions to `STOPPED_LATCHED`.
- Keeps reasserting Balance Stand while latched.
- Ignores repeated triggers after the first one.
- Moves to `FAULT` only for internal unrecoverable errors.

## Operator-Side Behavior

- Validates that `enp97s0` is the active operator NIC by default.
- Ignores common virtual interfaces such as `docker*`, `veth*`, `br-*`, `virbr*`, and `lxc*`.
- Uses a curses terminal UI.
- `Space` publishes a protective stop.
- `Esc` publishes a hard stop.
- `q` exits the operator client without affecting the robot latch.

## States

- `READY`
- `PROTECTIVE_STOPPING`
- `HARD_STOPPING`
- `STOPPED_LATCHED`
- `FAULT`

## Defaults

- Assertion rate: `5.0 Hz`
- Status publish rate: `2.0 Hz`
- Expected operator NIC: `enp97s0`
- Status stale timeout: `2.0 s`

## DDS Interface Binding

Robot-side deployment binds CycloneDDS to both:

- `wlan0` for operator communication
- `eth0` for communication with the Unitree sport service

Operator-side deployment binds CycloneDDS to:

- `enp97s0`

## Validation Goals

The implementation and scripts in this repository are intended to verify:

- the robot service reaches `READY`
- status continues publishing after latch
- protective and hard triggers are distinguishable in status
- the assertion loop runs at approximately 5 Hz
- quitting the operator client leaves the robot-side latch intact
- invalid NIC selection prevents operator startup
