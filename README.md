# Instructions


## Clone repo in here:
/ros2_ws/
rename repo to "src"

## How to run:
- Open 4 terminals
- cd into ~/ros2_ws/src/ on all the terminals
- source the terminals source install/setup.bash
- Terminal 1: ros2 launch tello_driver teleop_launch.py
- Terminal 2: ros2 launch yolo_bringup yolo.launch.py model:=/home/rasmus/Robotics/AerialRobotics/ros2_ws/models/gate_detection.pt input_image_topic:=/image_raw device:=cuda:0 image_reliability:=2
- Terminal 3: ros2 run drone_racing gate_analyzer
- Terminal 4: ros2 run drone_racing drone_controller


## Gate detection visualization:
To visualize the yolo gate detection you can use Rviz2 to display the yolo detections
- ros2 run rviz2 rviz2
- Add Image from /yolo/dbg_image
Note: Rviz2 may cause framedrops
