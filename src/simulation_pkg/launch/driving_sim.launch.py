#!/usr/bin/env python3

import os
import subprocess
from launch_ros.actions import Node
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
        
    subprocess.run(['killall', 'gzserver'])
    subprocess.run(['killall', 'gzclient'])
    
    package_dir=get_package_share_directory('simulation_pkg')
    world_file = os.path.join(package_dir, 'worlds', 'track.world')
    default_yolo_model = os.path.expanduser(
        '~/yolo/models/lane_segmentation/best.pt'
    )
        
    return LaunchDescription([
        DeclareLaunchArgument(
            'yolo_model',
            default_value=default_yolo_model,
            description='Path to the YOLO segmentation model'
        ),
        DeclareLaunchArgument(
            'yolo_device',
            default_value='cuda:0',
            description='YOLO inference device: auto, cpu, or cuda:0'
        ),

        ExecuteProcess(
            cmd=['gazebo', '--verbose', world_file, '-s', 'libgazebo_ros_factory.so'],
            output='screen'),
            
        ExecuteProcess(
            cmd=['rqt'], 
            output='screen'),
        
        # Node(
        #     package='simulation_pkg', 
        #     executable='video_recording_node',
        #     output='screen'
        # ),
        
        Node(
            package='simulation_pkg',
            executable='load_ego_car_node',
            output='screen'
        ),

        Node(
            package='camera_perception_pkg',
            executable='yolov8_node',
            output='screen',
            parameters=[{
                'model': LaunchConfiguration('yolo_model'),
                'device': LaunchConfiguration('yolo_device'),
                'threshold': 0.3,
            }],
            remappings=[
                ('image_raw', '/camera/image_raw'),
            ]
        ),

        Node(
            package='debug_pkg',
            executable='yolov8_visualizer_node',
            output='screen',
            remappings=[
                ('image_raw', '/camera/image_raw'),
            ]
        ),

        Node(
            package='debug_pkg',
            executable='path_visualizer_node',
            output='screen'
        ),
        
        Node(
            package='camera_perception_pkg', 
            executable='lane_info_extractor_node',
            output='screen',
            parameters=[{
                # stop_zone이 lane2를 가린 구간은 보이는 lane2 진행 방향으로
                # 연장한다. stop_zone 자체를 차선 장애물처럼 피하지 않는다.
                'stop_zone_boundary_exclusion_px': 10,
                'stop_zone_dashed_margin_px': 4,
                'stop_zone_bridge_history_weight': 0.35,
                'stop_zone_bridge_max_slope': 0.35,
                'stop_zone_smoothing_alpha': 0.18,
                'stop_zone_max_target_step_px': 6.0,
            }]
        ),
        Node(
            package='camera_perception_pkg',
            executable='traffic_light_detector_node',
            output='screen',
            parameters=[{
                'sub_image_topic': '/camera/image_raw',
            }]
        ),

        Node(
            package='decision_making_pkg', 
            executable='path_planner_node',
            output='screen'
        ),
       
        Node(
            package='decision_making_pkg', 
            executable='motion_planner_node',
            output='screen',
            parameters=[{
                # stop_zone을 처음 본 순간부터 감속하고, 통과 뒤에는 서서히
                # 가속해 다음 코너에서 제어 여유를 확보한다.
                'stop_zone_speed': 120,
                'stop_zone_speed_hold_sec': 1.2,
                'speed_recovery_step': 10,
            }]
        ),
       
        Node(
            package='simulation_pkg', 
            executable='sim_simulation_sender_node',
            output='screen'
        ),
                     
    ])
