# Finish SLAM toolbox map save

> we are trying to do mapping of a hallway using lidar in ros2 on a robot. the current commands we are using are in the cmds.txt file, and the rosbot folder is in the src. I need to save the lidar map as ~/b7_ws/Maps/brown_basement.[ENDING]. don't do anything, just tell me if anything is wrong and how to finish the slam_toolbox command. also will it append as it goes or what

<details><summary>4 previous messages</summary>

> I’ll read `cmds.txt` and the ROS configuration without changing anything, then check the map-saving command and how updates are saved.
>
> <details><summary>Searched the web</summary>
>
> Searched the web for `site.github.com SteveMacenski slam_toolbox SerializePoseGraph serialize_map SaveMap online_async_launch use_sim_time ...`
>
> Searched the web for `https://raw.githubusercontent.com/SteveMacenski/slam_toolbox/ros2/srv/SerializePoseGraph.srv`
>
> </details>
>
> The save command has a typo: `serialize_mal` should be `serialize_map`. That service saves the SLAM session for resuming mapping; a standard map image uses `.pgm` plus `.yaml`. Saving either is a snapshot—it does not keep updating the files as you drive.
>
> <details><summary>Searched the web</summary>
>
> Searched the web for `https://raw.githubusercontent.com/SteveMacenski/slam_toolbox/humble/launch/online_async_launch.py`
>
> Searched the web for `https://raw.githubusercontent.com/ros-navigation/navigation2/humble/nav2_map_server/src/map_io.cpp`
>
> </details>
</details>

I only inspected the files; nothing was changed or launched.

There are a few things to fix or check:

- In [cmds.txt:11](./cmds.txt:11), `serialize_mal` should be **`serialize_map`**, and the request is unfinished.
- **Use real robot time.** The Humble launch file defaults to simulation time, so your SLAM launch should be:
  ```bash
  ros2 launch slam_toolbox online_async_launch.py use_sim_time:=false
  ```
  [Upstream launch file](https://github.com/SteveMacenski/slam_toolbox/blob/humble/launch/online_async_launch.py)
- Your standalone lidar command **bypasses the filters** in `sensors_launch.py`. If you want those filters, use `ros2 launch rosbot sensors_launch.py` instead of separately starting lidar, camera, and RViz. Avoid running both lidar drivers.
- That sensors launch has an RViz path issue at [line 53](./src/rosbot/launch/sensors_launch.py:53): `os.path.join('~', ...)` does not expand `~`. The expression should be `os.path.expanduser('~/b7_ws/rviz_config.rviz')`.
- SLAM needs the robot’s odometry and TF connection through `odom → base_footprint → … → lidar_frame`. Your README says bringup starts automatically, so this may already be covered; these files alone cannot confirm it.

To **finish your existing serialization command**, run this in a sourced terminal on the robot, while SLAM is running:

```bash
mkdir -p ~/b7_ws/Maps

ros2 service call /slam_toolbox/serialize_map \
  slam_toolbox/srv/SerializePoseGraph \
  "{filename: '$HOME/b7_ws/Maps/brown_basement'}"
```

Give the filename **without an extension**. This produces **`brown_basement.posegraph` and `brown_basement.data`**, which together preserve the SLAM session for continuing mapping later. [Serialization implementation](https://github.com/SteveMacenski/slam_toolbox/blob/ros2/include/slam_toolbox/serialization.hpp)

For the **ordinary map image and configuration**, also run:

```bash
ros2 service call /slam_toolbox/save_map \
  slam_toolbox/srv/SaveMap \
  "{name: {data: '$HOME/b7_ws/Maps/brown_basement'}}"
```

This produces **`brown_basement.pgm` and `brown_basement.yaml`** in `~/b7_ws/Maps`. The service uses Nav2’s map saver, so `nav2_map_server` must be installed. A successful service response has `result: 0`. These service calls save on the computer running SLAM Toolbox. [Map-saving implementation](https://github.com/SteveMacenski/slam_toolbox/blob/humble/src/map_saver.cpp)

**It builds the live map as you drive, but does not continuously append to the saved files.** Each save captures the current state; saving again under the same name replaces the earlier snapshot. Save again after finishing, before shutting down SLAM. After restarting SLAM, continuing the previous session requires explicitly loading the serialized map; using the same save filename does not load it automatically. [SLAM Toolbox documentation](https://github.com/SteveMacenski/slam_toolbox#lifelong-mapping)

> okay so what is the order to run everything? and ill fix the sensors file

Once you fix `sensors_launch.py`, use this order. Your README says the robot’s base bringup starts automatically.

**First, in each terminal**, connect to the robot and source your workspace:

```bash
ssh ubuntu@192.168.149.1
cd ~/b7_ws
source install/setup.zsh
```

Use `setup.bash` instead if the robot’s shell is Bash.

1. **Terminal 1 — start the sensors and RViz.**

   After putting your corrected launch file on the robot, rebuild and source it:

   ```bash
   colcon build --packages-select rosbot
   source install/setup.zsh
   ros2 launch rosbot sensors_launch.py
   ```

   This starts lidar, the filters, the camera, and RViz. Leave it running.

2. **Terminal 2 — start SLAM.**

   ```bash
   ros2 launch slam_toolbox online_async_launch.py use_sim_time:=false
   ```

   Leave it running. In RViz, set **Fixed Frame** to `map`, add a **Map** display, and select `/map`.

3. **Terminal 3 — start your controller.**

   ```bash
   ros2 run rosbot teleop_joy
   ```

   Drive through the hallway while watching the map develop.

4. **Terminal 4 — save when you’re finished, while SLAM is still running.**

   Stop driving, allow the map display to update, then run:

   ```bash
   mkdir -p ~/b7_ws/Maps
   ```

   Save the map image and metadata (`.pgm` and `.yaml`):

   ```bash
   ros2 service call /slam_toolbox/save_map \
     slam_toolbox/srv/SaveMap \
     "{name: {data: '$HOME/b7_ws/Maps/brown_basement'}}"
   ```

   Save the resumable SLAM session (`.posegraph` and `.data`):

   ```bash
   ros2 service call /slam_toolbox/serialize_map \
     slam_toolbox/srv/SerializePoseGraph \
     "{filename: '$HOME/b7_ws/Maps/brown_basement'}"
   ```

   Check for `result: 0` and verify the files:

   ```bash
   ls -lh ~/b7_ws/Maps/brown_basement.*
   ```

**Save before stopping SLAM.** You can save checkpoints during mapping, but each save replaces that filename’s previous snapshot. If you drive farther afterward, save again to include the additional mapping.

> okay so what is the order to run everything? and ill fix the sensors file

> ge

> okay it only renders the first lidar and then stops. the yaml only contains one scan

<details><summary>7 previous messages</summary>

> I’ll check the current files for anything that could stop SLAM after its first scan. The saved `.yaml` normally contains map metadata; the `.pgm` contains the map image.
>
> While you drive, does the live map in RViz also stay frozen, and what warnings or errors appear in the terminal running SLAM Toolbox?
>
> <details><summary>Searched the web</summary>
>
> Searched the web for `https://raw.githubusercontent.com/SteveMacenski/slam_toolbox/humble/config/mapper_params_online_async.yaml`
>
> </details>
>
> <details><summary>Searched the web</summary>
>
> Searched the web for `https://raw.githubusercontent.com/SteveMacenski/slam_toolbox/humble/src/slam_toolbox_async.cpp`
>
> </details>
>
> **While you drive, does the live map in RViz also stay frozen, and what warnings or errors appear in the terminal running SLAM Toolbox?**
>
> the robot moves around but the only mapping is always just the first one
>
> That points to a problem with the live mapping, rather than just saving. If scans are still arriving, the next check is odometry: the robot can physically move while SLAM keeps receiving an unchanged position.
>
> <details><summary>Searched the web</summary>
>
> Searched the web for `'bool SlamToolbox::shouldProcessScan' in https://raw.githubusercontent.com/SteveMacenski/slam_toolbox/humble/src/slam_toolbox_common.cpp`
>
> </details>
</details>

Since the **live map stays at the first scan while the robot moves**, check whether scans keep arriving and whether SLAM sees the robot’s movement.

**One concrete concern:** your current `cmds.txt` lists both `sensors_launch.py` and the standalone `sllidar_node` command. **If you ran both, stop the extra standalone lidar process.** The sensors launch already starts it; two drivers can compete for the same USB device.

Keep sensors and SLAM running, then run these checks in a sourced terminal on the robot:

1. **Check that filtered lidar scans keep arriving:**

   ```bash
   ros2 topic hz /scan
   ```

   It should continuously print a rate. Press Ctrl+C after checking. If there’s no continuing output, check the raw scans:

   ```bash
   ros2 topic hz /scan_raw
   ```

   Raw scans arriving but no `/scan` points toward the filter; neither arriving points toward the lidar driver/device.

2. **Check that odometry changes while you drive:**

   ```bash
   ros2 run tf2_ros tf2_echo odom base_footprint
   ```

   Watch `Translation` while driving forward. **If the position stays fixed despite movement, that can explain exactly this symptom:** SLAM Toolbox accepts the first scan, then checks odometry movement before accepting more. Missing-transform errors also indicate a TF problem. [SLAM scan-processing code](https://github.com/SteveMacenski/slam_toolbox/blob/humble/src/slam_toolbox_common.cpp#L472)

3. **Verify the running SLAM node uses real time:**

   ```bash
   ros2 param get /slam_toolbox use_sim_time
   ```

   It should report `False`.

The saved YAML contains metadata pointing to the `.pgm`, rather than a list of scans. Its short length is normal. [Nav2 map format implementation](https://github.com/ros-navigation/navigation2/blob/humble/nav2_map_server/src/map_io.cpp#L509)

**Send me the `/scan` rate, whether `Translation` changes, and any warnings from the SLAM terminal.** Those will narrow down the cause without guessing at configuration changes.

> ```
> ros2 param get /slam_toolbox use_sim_time
> ```
>
> returned Node not found. the scan keeps arriving, and RVIz the map message count is going up every few seconds. the map builds by one lidar scan every like 2-3 mins. the translation is also changing normally

<details><summary>2 previous messages</summary>

> That narrows it down: scans and odometry are active, and map messages are being published. I’ll check how SLAM decides to accept a new scan and identify why `/slam_toolbox` isn’t resolving as the node name.
>
> <details><summary>Searched the web</summary>
>
> Searched the web for `https://raw.githubusercontent.com/SteveMacenski/slam_toolbox/humble/src/slam_toolbox_common.cpp`
>
> </details>
</details>

That makes a stopped lidar or frozen odometry less likely. **The map count can increase while SLAM republishes essentially the same map**—its publication timer runs separately from accepting new scans. [SLAM implementation](https://github.com/SteveMacenski/slam_toolbox/blob/humble/src/slam_toolbox_common.cpp#L260)

**First, identify the actual node publishing your map.** `Node not found` means that terminal cannot find the exact name `/slam_toolbox`; the node may have a different name or namespace.

Run these on the robot in a sourced terminal:

```bash
ros2 node list
ros2 topic info /map --verbose
ros2 topic info /scan --verbose
```

These show:

- The `/map` publisher’s **node name and namespace**.
- Whether multiple nodes are publishing conflicting maps.
- Which node receives `/scan`, and whether you have duplicate scan publishers.

Once you identify the SLAM node, dump its configuration, replacing the placeholder with its full name:

```bash
ros2 param dump /ACTUAL_SLAM_NODE_NAME
```

**Also check the scale of the odometry.** When the robot travels approximately **1 metre**, the reported horizontal position should change by approximately **1 metre**. Values merely changing doesn’t establish that their scale is correct.

The default Humble configuration has `minimum_travel_distance: 0.5` metres and `map_update_interval: 5.0` seconds. Small movements can therefore produce few new scans, but **a 2–3 minute delay while travelling several metres needs further diagnosis**. [Default configuration](https://github.com/SteveMacenski/slam_toolbox/blob/humble/config/mapper_params_online_async.yaml)

Paste the topic-info results, parameter dump, and any SLAM terminal warnings. That will let us distinguish a movement threshold issue from scan/TF timing problems or an unexpected map publisher.

> ```
> ros2 param get /slam_toolbox use_sim_time
> ```
>
> returned Node not found. the scan keeps arriving, and RVIz the map message count is going up every few seconds. the map builds by one lidar scan every like 2-3 mins. the translation is also changing normally

<details><summary>2 previous messages</summary>

> **The increasing map count can be repeated publications of the same map.** It doesn’t establish that SLAM is incorporating new scans.
>
> First resolve **`Node not found`**. In a sourced terminal on the robot, run:
>
> ```bash
> ros2 node list
> ros2 topic info /map --verbose
> ```
>
> The second command identifies the map publisher’s **node name and namespace**. Use that full name instead of `/slam_toolbox`:
>
> ```bash
> ros2 param dump /ACTUAL_NODE_NAME
> ```
>
> Paste those outputs along with any warnings from the SLAM terminal.
>
> Two things remain worth checking:
>
> - **Odometry scale:** driving approximately 1 metre should change the reported position by approximately 1 metre. The default SLAM configuration requires roughly **0.5 metres of displacement** before adding another scan. Small movements or incorrectly scaled odometry could explain infrequent additions. [Default parameters](https://github.com/SteveMacenski/slam_toolbox/blob/humble/config/mapper_params_online_async.yaml)
> - **Transform timing:** changing translation confirms current odometry exists, but SLAM needs a transform matching **each scan’s timestamp**. Messages such as `Failed to compute odom pose`, `extrapolation`, or `Message Filter dropping message` would point toward that problem. [Scan callback](https://github.com/SteveMacenski/slam_toolbox/blob/humble/src/slam_toolbox_async.cpp#L30)
>
> If you’re travelling several metres and it still takes minutes, that exceeds the normal five-second map publication interval; we need the actual node configuration and warnings to identify why.
>
> the translation is fine. [async_slam_toolbox_node-1] Registering sensor: [Custom Described Lidar]
> [async_slam_toolbox_node-1] LaserRangeScan contains 1079 range readings, expected 1078
> [async_slam_toolbox_node-1] LaserRangeScan contains 1081 range readings, expected 1078
> [async_slam_toolbox_node-1] LaserRangeScan contains 1079 range readings, expected 1078
> [async_slam_toolbox_node-1] LaserRangeScan contains 1077 range readings, expected 1078
> [async_slam_toolbox_node-1] LaserRangeScan contains 603 range readings, expected 1078
> [async_slam_toolbox_node-1] LaserRangeScan contains 603 range readings, expected 1078
> [async_slam_toolbox_node-1] LaserRangeScan contains 593 range readings, expected 1078
> [async_slam_toolbox_node-1] LaserRangeScan contains 602 range readings, expected 1078
> [async_slam_toolbox_node-1] LaserRangeScan contains 602 range readings, expected 1078
> [async_slam_toolbox_node-1] LaserRangeScan contains 603 range readings, expected 1078
> [async_slam_toolbox_node-1] LaserRangeScan contains 602 range readings, expected 1078
> [async_slam_toolbox_node-1] LaserRangeScan contains 603 range readings, expected 1078
> [async_slam_toolbox_node-1] LaserRangeScan contains 600 range readings, expected 1078
> [async_slam_toolbox_node-1] LaserRangeScan contains 602 range readings, expected 1078
> [async_slam_toolbox_node-1] LaserRangeScan contains 599 range readings, expected 1078
> [async_slam_toolbox_node-1] LaserRangeScan contains 601 range readings, expected 1078
> [async_slam_toolbox_node-1] LaserRangeScan contains 602 range readings, expected 1078
> [async_slam_toolbox_node-1] LaserRangeScan contains 601 range readings, expected 1078
> [async_slam_toolbox_node-1] LaserRangeScan contains 602 range readings, expected 1078
> [async_slam_toolbox_node-1] LaserRangeScan contains 601 range readings, expected 1078
> ^C[WARNING] [launch]: user interrupted with ctrl-c (SIGINT)
> [async_slam_toolbox_node-1] [INFO] [0000003651.931705504] [rclcpp]: signal_handler(signum=2)
> [INFO] [async_slam_toolbox_node-1]: process has finished cleanly [pid 7302]
>  ~/b7_ws                                                    4m 26s | ubuntu@/ | 09:00:52
> > ros2 launch slam_toolbox online_async_launch.py use_sim_time:=false
>
> [async_slam_toolbox_node-1] LaserRangeScan contains 600 range readings, expected 1078
> [async_slam_toolbox_node-1] LaserRangeScan contains 602 range readings, expected 1078
> [async_slam_toolbox_node-1] LaserRangeScan contains 599 range readings, expected 1078
> [async_slam_toolbox_node-1] LaserRangeScan contains 601 range readings, expected 1078
> [async_slam_toolbox_node-1] LaserRangeScan contains 602 range readings, expected 1078
> [async_slam_toolbox_node-1] LaserRangeScan contains 601 range readings, expected 1078
> [async_slam_toolbox_node-1] LaserRangeScan contains 602 range readings, expected 1078
> [async_slam_toolbox_node-1] LaserRangeScan contains 601 range readings, expected 1078
> ^C[WARNING] [launch]: user interrupted with ctrl-c (SIGINT)
> [async_slam_toolbox_node-1] [INFO] [0000003651.931705504] [rclcpp]: signal_handler(signum=2)
> [INFO] [async_slam_toolbox_node-1]: process has finished cleanly [pid 7302]
> > ros2 launch slam_toolbox online_async_launch.py use_sim_time:=false
> [INFO] [launch]: All log files can be found below /home/ubuntu/.ros/log/1970-01-01-09-01-25-449490-ubuntu-8278
> [INFO] [launch]: Default logging verbosity is set to INFO
> [INFO] [async_slam_toolbox_node-1]: process started with pid [8279]
> [async_slam_toolbox_node-1] [INFO] [0000003685.660569824] [slam_toolbox]: Node using stack size 40000000
> [async_slam_toolbox_node-1] [INFO] [0000003685.887881120] [slam_toolbox]: Using solver plugin solver_plugins::CeresSolver
> [async_slam_toolbox_node-1] [INFO] [0000003685.890886944] [slam_toolbox]: CeresSolver: Using SCHUR_JACOBI preconditioner.
> [async_slam_toolbox_node-1] [WARN] [0000003686.758108096] [slam_toolbox]: minimum laser range setting (0.0 m) exceeds the capabilities of the used Lidar (0.1 m)
> [async_slam_toolbox_node-1] [WARN] [0000003686.758429152] [slam_toolbox]: maximum laser range setting (20.0 m) exceeds the capabilities of the used Lidar (12.0 m)
> [async_slam_toolbox_node-1] Registering sensor: [Custom Described Lidar]
> [async_slam_toolbox_node-1] LaserRangeScan contains 602 range readings, expected 593
> [async_slam_toolbox_node-1] LaserRangeScan contains 595 range readings, expected 593
> [async_slam_toolbox_node-1] LaserRangeScan contains 600 range readings, expected 593
>
> User context
>
> Attachments:
> - > ros2 node list /arm_controller /controller_manager /depth_cam/camera_containe…: `~/.codex/attachments/6c8686dd-1dc2-4436-9d52-09801d616d20/Pasted text.txt`
</details>

Those errors give us a concrete cause to investigate: SLAM is seeing a different number of lidar readings from what it registered initially. I’ll check your driver’s scan settings and the pasted node information to identify the fix.

> i already ran that command
>
> User context
>
> Attachments:
> - > ros2 node list /arm_controller /controller_manager /depth_cam/camera_containe…: `~/.codex/attachments/2c1147a5-3cf7-493e-a25d-776c72ebd8d1/Pasted text.txt`

<details><summary>3 previous messages</summary>

> You did—sorry for asking you to repeat it. Your output confirms the node, topics, and clock setting are correct. The range-count errors are the useful clue now; I’m checking the lidar driver for the setting that stabilizes scan size.
>
> <details><summary>Searched the web</summary>
>
> Searched the web for `site.github.com/SteveMacenski/slam_toolbox "LaserRangeScan contains" "angle_compensate" ...`
>
> </details>
>
> <details><summary>Searched the web</summary>
>
> Searched the web for `https://raw.githubusercontent.com/SteveMacenski/slam_toolbox/humble/lib/karto_sdk/src/Karto.cpp`
>
> </details>
</details>

**The range-count errors identify the problem:** SLAM registers one scan size, then rejects scans with different sizes. That explains the occasional map updates. [SLAM validation code](https://github.com/SteveMacenski/slam_toolbox/blob/humble/lib/karto_sdk/src/Karto.cpp#L193)

Your lidar driver defaults **`angle_compensate` to `false`**, and your launch file omits it. Enabling it makes the driver publish a consistent number of readings.

In [sensors_launch.py](./src/rosbot/launch/sensors_launch.py:19), add this inside the **lidar node’s parameters dictionary**, beside `frame_id`:

```python
"frame_id": "lidar_frame",
"angle_compensate": True,
```

Then:

1. Stop **SLAM and the sensors launch** with Ctrl+C.
2. Put the edited file on the robot, then rebuild and launch sensors:

   ```bash
   cd ~/b7_ws
   colcon build --packages-select rosbot
   source install/setup.zsh
   ros2 launch rosbot sensors_launch.py
   ```

3. In another sourced terminal, restart SLAM:

   ```bash
   ros2 launch slam_toolbox online_async_launch.py use_sim_time:=false
   ```

**Restarting SLAM matters:** it must register the new, consistent scan size instead of retaining the old expected count.

The `LaserRangeScan contains … expected …` messages should stop, and mapping should update as you drive. Your pasted results already confirm one publisher per topic and `use_sim_time: false`; those checks are settled. I haven’t changed any files.

