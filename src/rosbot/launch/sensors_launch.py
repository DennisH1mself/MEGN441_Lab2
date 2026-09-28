import os
from ament_index_python.packages import get_package_share_directory
import launch
import launch_ros.actions
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    # Find the location of the package on your computer
    camera_pkg_path = get_package_share_directory('orbbec_camera')
    rosbot_pkg_path = get_package_share_directory('rosbot')
    laser_filters_config = os.path.join(rosbot_pkg_path, 'config/lidar_filters_config_a1.yaml')

    lidar = launch_ros.actions.Node(
        package='sllidar_ros2',
        executable='sllidar_node',
        name='sllidar_node',
        # Don't edit the remapping.
        # It is needed for the lidar filter included below.
        parameters=[{
            "serial_port": "/dev/ttyCH341USB0",
            "serial_baudrate": 115200,
            "frame_id": "lidar_frame",
        }],
        remappings=[('scan', 'scan_raw')]
    )


    camera_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(camera_pkg_path, 'launch/dabai_dcw.launch.py')),
            launch_arguments = {"camera_name": "depth_cam", "publish_tf": "true"}.items()
    )

    laser_filter = launch_ros.actions.Node(
            package='laser_filters',
            executable='scan_to_scan_filter_chain',
            output='screen',
            parameters=[laser_filters_config],
            remappings=[('scan', 'scan_raw'),
                        ('scan_filtered', 'scan')]
        )

    # TODO: Launch rviz. 

    # Your final returned LaunchDescription includes 
    # a list of all of the nodes, launch files, etc.

    rviz = launch_ros.actions.Node(
        package='rviz2',
        executable='rviz2',
        output='screen',
        arguments=[
            "-d", os.path.join('~', 'b7_ws/rviz_config.rviz')
        ]
    )
    return launch.LaunchDescription([
        lidar,
        laser_filter,
        camera_launch,
        rviz,
    ])


if __name__ == '__main__':
    # Create a LaunchDescription object
    ld = generate_launch_description()

    ls = launch.LaunchService()
    ls.include_launch_description(ld)
    ls.run()
