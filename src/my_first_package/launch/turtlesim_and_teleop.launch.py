from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='my_first_package',
            executable='dist_turtle_action_server',
            name='dist_turtle_action_server', # 실행 시 노드 이름 지정
            output='screen'
        ),
        Node(
            package='turtlesim',
            executable='turtlesim_node',
            name='turtlesim_node',
            output='screen',
            parameters=[
                {'background_r': 255},
                {'background_g': 255}, 
                {'background_b': 255}]
        ),
        Node(
            package='my_first_package',
            executable='my_publisher',
            name='pub_cmd_vel',
            output='screen' 
        )
    ])