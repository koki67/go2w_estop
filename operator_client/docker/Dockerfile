FROM ros:humble-ros-base

RUN apt-get update && apt-get install -y --no-install-recommends \
      ros-humble-rmw-cyclonedds-cpp \
      ros-humble-rosidl-generator-dds-idl \
      python3-colcon-common-extensions \
    && rm -rf /var/lib/apt/lists/*

COPY estop_interfaces/ /ros2_ws/src/estop_interfaces/
COPY operator_client/ /ros2_ws/src/go2w_estop_operator/

WORKDIR /ros2_ws

RUN /bin/bash -c "source /opt/ros/humble/setup.bash && colcon build --packages-up-to go2w_estop_operator"

COPY operator_client/docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["ros2", "launch", "go2w_estop_operator", "operator_client.launch.py"]
