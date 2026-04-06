#!/usr/bin/env python3
"""Launch the operator-side e-stop client."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_dir = get_package_share_directory("go2w_estop_operator")
    default_params = os.path.join(pkg_dir, "config", "operator_client_params.yaml")

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "params_file",
                default_value=default_params,
                description="Path to operator client parameters YAML",
            ),
            DeclareLaunchArgument(
                "expected_nic",
                default_value="enp97s0",
                description="Required operator NIC",
            ),
            DeclareLaunchArgument(
                "validate_nic_on_startup",
                default_value="true",
                description="Enforce NIC validation before starting the UI",
            ),
            Node(
                package="go2w_estop_operator",
                executable="operator_client",
                name="go2w_estop_operator_node",
                parameters=[
                    LaunchConfiguration("params_file"),
                    {
                        "expected_nic": LaunchConfiguration("expected_nic"),
                        "validate_nic_on_startup": LaunchConfiguration(
                            "validate_nic_on_startup"
                        ),
                    },
                ],
                output="screen",
            ),
        ]
    )
