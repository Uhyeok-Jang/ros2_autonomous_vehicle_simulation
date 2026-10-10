#!/usr/bin/env python3

import os
from launch_ros.actions import Node
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
        
    
    package_dir=get_package_share_directory('simulation_pkg')
    world_file = os.path.join(package_dir, 'worlds', 'track.world')
    default_yolo_model = os.path.join(package_dir, 'data', 'sim.pt')
        
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
                'lane_threshold': 0.15,
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
            executable='lane_tracking_visualizer_node',
            output='screen',
            remappings=[('image_raw', '/camera/image_raw')]
        ),

        Node(
            package='debug_pkg',
            executable='path_visualizer_node',
            output='screen'
        ),
        
        Node(
            package='camera_perception_pkg', 
            executable='lane_info_extractor_node',
            output='screen'
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
                # Match the current real-vehicle controller settings.
                'driving_speed': 245,
                'lane_loss_speed': 180,
                'lane_detection_timeout': 0.2,
                'kp_heading': 0.09,
                'steering_alpha': 1.0,
                'max_steering_step': 4.0,
                'timer': 0.1,
            }]
        ),
       
        Node(
            package='simulation_pkg', 
            executable='sim_simulation_sender_node',
            output='screen'
        ),
                     
    ])
