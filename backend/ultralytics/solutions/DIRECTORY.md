# `backend/ultralytics/solutions` 目录说明

## 目录定位
YOLO 推理所需的 Ultralytics 代码/资源（包含配置与数据集结构；主要作为第三方依赖随项目打包）。

[上级目录](../DIRECTORY.md)

## 本目录文件概览
- `__init__.py`
- `ai_gym.py`
- `analytics.py`
- `distance_calculation.py`
- `heatmap.py`
- `object_counter.py`
- `parking_management.py`
- `queue_management.py`
- `region_counter.py`
- `security_alarm.py`
- `solutions.py`
- `speed_estimation.py`
- `streamlit_inference.py`
- `trackzone.py`

## 脚本/模块说明（本目录内）
### `__init__.py`
- 作用/意义: Ultralytics 🚀 AGPL-3.0 License - https://ultralytics.com/license
- 路径: `backend/ultralytics/solutions/__init__.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/cfg/__init__.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/__init__.py`

### `ai_gym.py`
- 作用/意义: A class to manage gym steps of people in a real-time video stream based on their poses.
- 路径: `backend/ultralytics/solutions/ai_gym.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `backend/ultralytics/solutions/solutions.py`
- `backend/ultralytics/utils/plotting.py`

### `analytics.py`
- 作用/意义: A class for creating and updating various types of charts for visual analytics.
- 路径: `backend/ultralytics/solutions/analytics.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `backend/ultralytics/solutions/solutions.py`

**引用了谁（外部依赖）**
- `cv2`
- `itertools`
- `matplotlib`
- `numpy`

### `distance_calculation.py`
- 作用/意义: A class to calculate distance between two objects in a real-time video stream based on their tracks.
- 路径: `backend/ultralytics/solutions/distance_calculation.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `backend/ultralytics/solutions/solutions.py`
- `backend/ultralytics/utils/plotting.py`

**引用了谁（外部依赖）**
- `cv2`
- `math`

### `heatmap.py`
- 作用/意义: A class to draw heatmaps in real-time video streams based on object tracks.
- 路径: `backend/ultralytics/solutions/heatmap.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `backend/ultralytics/solutions/object_counter.py`
- `backend/ultralytics/utils/plotting.py`

**引用了谁（外部依赖）**
- `cv2`
- `numpy`

### `object_counter.py`
- 作用/意义: A class to manage the counting of objects in a real-time video stream based on their tracks.
- 路径: `backend/ultralytics/solutions/object_counter.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/solutions/heatmap.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/solutions/solutions.py`
- `backend/ultralytics/utils/plotting.py`

### `parking_management.py`
- 作用/意义: A class for selecting and managing parking zone points on images using a Tkinter-based UI.
- 路径: `backend/ultralytics/solutions/parking_management.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `backend/ultralytics/solutions/solutions.py`
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/checks.py`
- `backend/ultralytics/utils/plotting.py`

**引用了谁（外部依赖）**
- `PIL`
- `cv2`
- `io`
- `json`
- `numpy`
- `tkinter`

### `queue_management.py`
- 作用/意义: Manages queue counting in real-time video streams based on object tracks.
- 路径: `backend/ultralytics/solutions/queue_management.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `backend/ultralytics/solutions/solutions.py`
- `backend/ultralytics/utils/plotting.py`

### `region_counter.py`
- 作用/意义: A class designed for real-time counting of objects within user-defined regions in a video stream.
- 路径: `backend/ultralytics/solutions/region_counter.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `backend/ultralytics/solutions/solutions.py`
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/plotting.py`

### `security_alarm.py`
- 作用/意义: A class to manage security alarm functionalities for real-time monitoring.
- 路径: `backend/ultralytics/solutions/security_alarm.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `backend/ultralytics/solutions/solutions.py`
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/plotting.py`

**引用了谁（外部依赖）**
- `cv2`
- `email`
- `smtplib`

### `solutions.py`
- 作用/意义: A base class for managing Ultralytics Solutions.
- 路径: `backend/ultralytics/solutions/solutions.py`

**被谁引用/调用（代码级）**
- `backend/ultralytics/solutions/ai_gym.py`
- `backend/ultralytics/solutions/analytics.py`
- `backend/ultralytics/solutions/distance_calculation.py`
- `backend/ultralytics/solutions/object_counter.py`
- `backend/ultralytics/solutions/parking_management.py`
- `backend/ultralytics/solutions/queue_management.py`
- `backend/ultralytics/solutions/region_counter.py`
- `backend/ultralytics/solutions/security_alarm.py`
- `backend/ultralytics/solutions/speed_estimation.py`
- `backend/ultralytics/solutions/trackzone.py`

**引用了谁（内部依赖）**
- `backend/ultralytics/__init__.py`
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/checks.py`
- `backend/ultralytics/utils/downloads.py`

**引用了谁（外部依赖）**
- `collections`
- `cv2`
- `shapely`

### `speed_estimation.py`
- 作用/意义: A class to estimate the speed of objects in a real-time video stream based on their tracks.
- 路径: `backend/ultralytics/solutions/speed_estimation.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `backend/ultralytics/solutions/solutions.py`
- `backend/ultralytics/utils/plotting.py`

**引用了谁（外部依赖）**
- `numpy`
- `time`

### `streamlit_inference.py`
- 作用/意义: A class to perform object detection, image classification, image segmentation and pose estimation inference using     Streamlit and Ultralytics YOLO models. It provides the functionalities such as loading models, configuring settings,     uploading video files, and performing real-time inference.
- 路径: `backend/ultralytics/solutions/streamlit_inference.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `backend/ultralytics/__init__.py`
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/checks.py`
- `backend/ultralytics/utils/downloads.py`

**引用了谁（外部依赖）**
- `cv2`
- `io`
- `streamlit`
- `sys`
- `typing`

### `trackzone.py`
- 作用/意义: A class to manage region-based object tracking in a video stream.
- 路径: `backend/ultralytics/solutions/trackzone.py`

**被谁引用/调用（代码级）**
（无）

**引用了谁（内部依赖）**
- `backend/ultralytics/solutions/solutions.py`
- `backend/ultralytics/utils/plotting.py`

**引用了谁（外部依赖）**
- `cv2`
- `numpy`

## 引用关系（目录级汇总）
**本目录被谁引用（跨目录）**
- `backend/ultralytics/cfg/__init__.py`

**本目录引用了谁（跨目录）**
- `backend/ultralytics/__init__.py`
- `backend/ultralytics/utils/__init__.py`
- `backend/ultralytics/utils/checks.py`
- `backend/ultralytics/utils/downloads.py`
- `backend/ultralytics/utils/plotting.py`
