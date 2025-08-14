import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

import xacro


def generate_launch_description():

    # é para dar match com o nome do arquivo .xacro
    robotXacroName = "differential_drive_robot"

    # Nome do pacote, ao mesmo tempo é o nome do folder que vai ser usado para definir o path
    namePackage = "mobile_robot"

    # relative path do arquivo xacro definindo do model
    modelFileRelativePath = "model/robot.xacro"

    # definir o absolute path do model
    pathModelFile = os.path.join(
        get_package_share_directory(namePackage), modelFileRelativePath
    )

    # converter o arquivo xacro em xml
    robotDescription = xacro.process_file(pathModelFile).toxml()

    # launch file para o gazebo_ros package
    gazebo_rosPackageLaunch = PythonLaunchDescriptionSource(
        os.path.join(
            get_package_share_directory("ros_gz_sim"), "launch", "gz_sim.launch.py"
        )
    )

    # usando um empty model world para gazebo
    gazeboLaunch = IncludeLaunchDescription(
        gazebo_rosPackageLaunch,
        launch_arguments={
            "gz_args": "-r -v -v4 empty.sdf",
            "on_exit_shutdown": "true",
        }.items(),
    )

    # Gazebo node
    spawnModelNodeGazebo = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=["-name", robotXacroName, "-topic", "robot_description"],
        output="screen",
    )

    # robot state publisher node
    nodeRobotStatePublisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[{"robot_description": robotDescription, "use_sim_time": True}],
    )

    # parametros para gazebo bridge
    bridge_params = os.path.join(
        get_package_share_directory(namePackage), "parameters", "bridge_parameters.yaml"
    )

    start_gazebo_ros_bridge_cmd = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "--ros-args",
            "-p",
            f"config_file:={bridge_params}",
        ],
        output="screen",
    )

    # Criar um node do bridge para cmd_vel
    bridge_cmd_vel = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "/model/differential_drive_robot/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist"
        ],
        output="screen",
    )

    # criar a launch description vazio
    launchDescriptionObject = LaunchDescription()

    # adicionar gazebo launch
    launchDescriptionObject.add_action(gazeboLaunch)

    # adicionar o node do gazebo
    launchDescriptionObject.add_action(nodeRobotStatePublisher)
    launchDescriptionObject.add_action(spawnModelNodeGazebo)
    launchDescriptionObject.add_action(start_gazebo_ros_bridge_cmd)
    launchDescriptionObject.add_action(bridge_cmd_vel)

    return launchDescriptionObject
