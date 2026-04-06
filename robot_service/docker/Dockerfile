FROM ros:humble-ros-base

RUN apt-get update && apt-get install -y --no-install-recommends \
      ros-humble-rmw-cyclonedds-cpp \
      ros-humble-rosidl-generator-dds-idl \
      python3-colcon-common-extensions \
      git \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 https://github.com/koki67/unitree_ros2.git \
      /ros2_ws/src/unitree_ros2 \
    && rm -rf /ros2_ws/src/unitree_ros2/.git

COPY estop_interfaces/ /ros2_ws/src/estop_interfaces/
COPY robot_service/ /ros2_ws/src/go2w_estop_robot/

WORKDIR /ros2_ws

RUN /bin/bash -c "source /opt/ros/humble/setup.bash && colcon build --packages-up-to go2w_estop_robot"

COPY robot_service/docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["ros2", "launch", "go2w_estop_robot", "robot_service.launch.py"]
