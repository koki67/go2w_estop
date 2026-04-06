#!/usr/bin/env python3
"""Launch the robot-side e-stop service."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_dir = get_package_share_directory("go2w_estop_robot")
    default_params = os.path.join(pkg_dir, "config", "robot_service_params.yaml")

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "params_file",
                default_value=default_params,
                description="Path to robot service parameters YAML",
            ),
            Node(
                package="go2w_estop_robot",
                executable="robot_service",
                name="go2w_estop_robot_node",
                parameters=[LaunchConfiguration("params_file")],
                output="screen",
            ),
        ]
    )
