# Third-Party Notices

This repository includes third-party code as a git submodule:

## `third_party/unitree_ros2`

- Source: <https://github.com/koki67/unitree_ros2>
- Integrated as: git submodule
- Purpose in this repository: provides the `unitree_api` ROS 2 message package used by `go2w_estop_robot`
- Upstream license metadata:
  - GitHub repository license: BSD 3-Clause
  - `cyclonedds_ws/src/unitree/unitree_api/package.xml`: `BSD 3-Clause License`
  - Submodule top-level `LICENSE`: BSD 3-Clause

License handling:

- The submodule keeps its own git history and upstream `LICENSE` file.
- This repository does not relicense `unitree_ros2`.
- Redistributors should preserve the submodule's license notice when shipping source or binaries that include it.

The `go2w_estop` code in this repository is separate from `unitree_ros2` and is licensed under this repository's own [`LICENSE`](LICENSE).
