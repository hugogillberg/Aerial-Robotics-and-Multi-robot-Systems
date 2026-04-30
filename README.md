# Instructions


## Clone repo in here:
/ros2_ws/

rename cloned folder to "src"

## How to run:
- Open 4 terminals
- Cd into ~/ros2_ws/ on all the terminals
- Build with colcon build
- Source the terminals source install/setup.bash
- Terminal 1: ros2 launch tello_driver teleop_launch.py
- Terminal 2: ros2 launch yolo_bringup yolo.launch.py model:=/ABSOLUTE_PATH_TO_ROS_WORKSPACE/models/gate_detection.pt input_image_topic:=/image_raw device:=cuda:0 image_reliability:=2
- Terminal 3: ros2 run drone_racing gate_analyzer
- Terminal 4: ros2 run drone_racing drone_controller


## Gate detection visualization:
To visualize the yolo gate detection you can use Rviz2 to display the yolo detections
- ros2 run rviz2 rviz2
- Add Image from /yolo/dbg_image

Note: Rviz2 may cause dropped frames




https://docs.google.com/document/d/1uxUaTbAPHDvPYgQyUM8kqddHJv-b2u44QmtcUymiOME/edit?usp=sharing
