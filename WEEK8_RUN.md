# Week 8 lane-following snapshot

This branch records the current lane2 controller and perception/target-path overlays. The controller waits for its first valid lane path, then preserves that path and reduces PWM during lane2 loss or stale perception. Red-light and obstacle stop conditions remain in the controller.

Current launch values: `driving_speed=245`, `lane_loss_speed=180`, `lane_detection_timeout=0.2`, `kp_heading=0.09`, `steering_alpha=1.0`, `max_steering_step=4.0`, `timer=0.1`. Edit the motion-planner parameters in the launch file for tuning.

Build from the workspace root with ROS2 Humble and the required Python/ROS dependencies installed:

```bash
source /opt/ros/humble/setup.bash
colcon build --symlink-install
./run_driving_sim.sh
```

The runner selects this workspace without the other workspace's overlay.

The driving launch is `src/simulation_pkg/launch/driving_sim.launch.py`. The mission launch is `src/simulation_pkg/launch/mission_sim.launch.py` and uses the same motion settings. Gazebo camera input and the existing PWM/steering-to-simulator mapping remain in place.

The model is committed at `src/simulation_pkg/simulation_pkg/data/sim.pt`, with metadata in `sim.json`. Building installs this file into the package share directory. Override it with `./run_driving_sim.sh yolo_model:=/absolute/path/to/model.pt`. Model SHA256: `8444c0351c789cc137d8f410f81c8383a4834b801a64d1746d8de55ff2b09643`.

Validation: 32 behavior/image tests and both launches checked with the synchronized settings. Gazebo track driving was not run during the snapshot preparation.
