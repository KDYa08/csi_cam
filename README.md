# CSI Camera ROS2 Publisher (Raspberry Pi 5)

## 📌 개요
이 프로젝트는 **Raspberry Pi 5에 연결된 CSI 카메라 영상을 ROS 2 토픽으로 퍼블리시하는 ROS 2 패키지**입니다.  
Ubuntu 24.04 및 **ROS 2 Jazzy Jalisco** 환경에서 테스트되었으며,  
**libcamera 기반 CSI 카메라 영상**을 실시간으로 ROS 2 노드에서 사용할 수 있도록 합니다.

카메라 영상은 ROS 2 이미지 메시지(`sensor_msgs/Image`) 형태로 퍼블리시되며,  
`rqt`, `image_view` 등 다양한 ROS 2 도구에서 확인할 수 있습니다.

---

## 🖥 테스트 환경
- **하드웨어**: Raspberry Pi 5  
- **운영체제**: Ubuntu 24.04  
- **ROS 2**: Jazzy Jalisco  
- **카메라**: CSI Camera (OV5647)  
- **카메라 프레임워크**: libcamera  

---

## 🔧 이 프로젝트가 하는 일
1. Raspberry Pi용 **libcamera**를 직접 빌드 및 설치
2. **rpicam-apps**를 통해 CSI 카메라 정상 동작 여부 확인
3. ROS 2 패키지 `csi_cam`을 사용하여
   - CSI 카메라 영상 캡처
   - 영상을 ROS 2 토픽으로 퍼블리시
4. ROS 2 환경에서 실시간 영상 처리 및 시각화 가능

---

## 📦 설치 방법

### 1️⃣ 필수 패키지 설치
```bash
sudo apt install -y build-essential libboost-dev libgnutls28-dev openssl \
libtiff-dev pybind11-dev qtbase5-dev libqt5core5a libqt5widgets5t64 \
meson cmake python3-yaml python3-ply
````

---

### 2️⃣ libcamera 빌드 및 설치

```bash
cd ~/colcon_ws/src
git clone https://github.com/raspberrypi/libcamera.git
cd libcamera

meson setup build --buildtype=release \
  -Dpipelines=rpi/vc4,rpi/pisp \
  -Dipas=rpi/vc4,rpi/pisp \
  -Dv4l2=true \
  -Dgstreamer=disabled \
  -Dtest=false \
  -Dlc-compliance=disabled \
  -Dcam=enabled \
  -Dqcam=disabled \
  -Ddocumentation=disabled \
  -Dpycamera=enabled

ninja -C build
sudo ninja -C build install
```

🔗 **libcamera 저장소**
[https://github.com/raspberrypi/libcamera](https://github.com/raspberrypi/libcamera)

* Raspberry Pi CSI 카메라를 제어하기 위한 **저수준 카메라 프레임워크**
* 카메라 센서 초기화, 스트림 제어, 이미지 캡처 담당
* `rpicam-apps` 및 `csi_cam`의 **기본 의존 라이브러리**

---

### 3️⃣ rpicam-apps 빌드 및 설치

```bash
cd ~/colcon_ws/src
git clone https://github.com/raspberrypi/rpicam-apps.git
cd rpicam-apps

sudo apt install -y cmake libboost-program-options-dev libdrm-dev \
libexif-dev ffmpeg libavcodec-extra libavcodec-dev libavdevice-dev \
libpng-dev libpng-tools libepoxy-dev qt5-qmake qtmultimedia5-dev

meson setup build \
  -Denable_libav=disabled \
  -Denable_drm=enabled \
  -Denable_egl=enabled \
  -Denable_qt=enabled \
  -Denable_opencv=disabled \
  -Denable_tflite=disabled \
  -Denable_hailo=disabled

meson compile -C build
sudo meson install -C build
sudo ldconfig
```

🔗 **rpicam-apps 저장소**
[https://github.com/raspberrypi/rpicam-apps](https://github.com/raspberrypi/rpicam-apps)

* libcamera 기반의 **카메라 테스트 및 예제 애플리케이션**
* `rpicam-still`, `rpicam-vid` 등을 제공
* ROS 실행 전 CSI 카메라가 정상 동작하는지 확인하는 용도

---

### 4️⃣ ROS 2 패키지 다운로드

```bash
cd ~/colcon_ws/src
git clone -b jazzy https://github.com/ros-perception/image_transport_plugins.git
sudo apt-get install ros-jazzy-image-transport-plugins
sudo apt update
sudo apt upgrade
git clone https://github.com/KDYa08/csi_cam.git
```

🔗 **image_transport_plugins**
[https://github.com/ros-perception/image_transport_plugins](https://github.com/ros-perception/image_transport_plugins)

* ROS 2에서 이미지 데이터를 효율적으로 전송하기 위한 플러그인 모음
* `raw`, `compressed` 등 다양한 image transport 방식 지원

🔗 **csi_cam**
[https://github.com/KDYa08/csi_cam](https://github.com/KDYa08/csi_cam.git)
* libcamera를 통해 CSI 카메라 영상을 획득
* 획득한 영상을 ROS 2 토픽(`sensor_msgs/Image`), (`sensor_msgs/CompressedImage`)으로 퍼블리시

---

### 5️⃣ ROS 2 워크스페이스 빌드

```bash
cd ~/colcon_ws
colcon build --symlink-install
source install/setup.bash
```

---

## ⚙️ CSI 카메라 설정

펌웨어 설정 파일 수정:

```bash
sudo nano /boot/firmware/config.txt
```

`[All]` 항목 아래에서 다음과 같이 수정합니다.

### GPU 메모리 설정

```ini
dtoverlay=vc4-kms-v3d,cma-384
```

또는

```ini
dtoverlay=vc4-kms-v3d,cma-512
```

### CSI 카메라 설정

```ini
dtoverlay=ov5647,cam0
```

카메라를 2개 사용하는 경우:

```ini
dtoverlay=ov5647,cam0
dtoverlay=ov5647,cam1
```

설정 후 재부팅:

```bash
sudo reboot
```

---

## 🧪 ROS 실행 전 카메라 테스트

연결된 카메라 확인:

```bash
cam -l
```

라이브러리 경로 설정:

```bash
export LD_LIBRARY_PATH=/usr/local/lib/aarch64-linux-gnu:$LD_LIBRARY_PATH
```

카메라 영상 테스트:

```bash
rpicam-still -t 0
```

## 에러 발생시
다음과 같은 에러가 발생한다면, 사용자가 video그룹에 포함되어있는지 확인

```bash
dmaheap allocation failure for rpicam-apps0 error: *** failed to allocate capture buffers for stream ***
```

```bash
groups user_name
```

만약 video그룹이 존재하지 않는다면 video그룹을 추가하고 재부팅 후, 다시 실행

```bash
sudo usermod -a -G video $USER
sudo reboot
```

---

## 📐 카메라 캘리브레이션 (Camera Calibration)

CSI 카메라의 렌즈 왜곡 보정 및 정확한 영상 처리를 위해 **체커보드 기반 카메라 캘리브레이션**을 수행할 수 있습니다.
본 프로젝트에는 이를 위한 Python 스크립트가 포함되어 있습니다.

---

### 1️⃣ 캘리브레이션 디렉토리 이동

```bash
cd ~/csi_cam/calibration
```

---

### 2️⃣ 캘리브레이션 스크립트 수정

```bash
nano calibration2.py
```

체커보드 설정을 **사용 중인 체커보드 규격에 맞게 수정**합니다.

#### ✔ 체커보드 내부 코너 개수 설정

```python
CHECKERBOARD = (7, 10)
```

#### ✔ 한 칸의 실제 길이 설정 (단위: mm)

```python
objp[0,:,:2] = np.mgrid[0:CHECKERBOARD[0], 0:CHECKERBOARD[1]].T.reshape(-1, 2) * 22 <-- 22mm
```

> 🔹 위 예시는 **한 칸당 22mm** 체커보드를 사용하는 경우입니다.
> 사용하는 체커보드에 맞게 반드시 수정하세요.

---

### 3️⃣ 체커보드 이미지 저장 폴더 생성

체커보드 이미지 저장용 폴더가 없다면 생성합니다.

```bash
mkdir checkerboards
```

---

### 4️⃣ 캘리브레이션 스크립트 실행

```bash
python3 calibration2.py
```

---

### 5️⃣ 체커보드로 캘리브레이션 진행

* 카메라 앞에 체커보드를 다양한 각도와 위치로 이동
* 충분한 프레임을 수집하고 q누르면 학습 진행
* 캘리브레이션 결과는 `.pkl` 파일로 저장됨

---

### 6️⃣ CSI 카메라 노드에 캘리브레이션 파일 적용

CSI 카메라 노드 소스 디렉토리로 이동합니다.

```bash
cd ~/csi_cam/csi_cam
```

소스 파일을 수정합니다.

```bash
nano csi_cam_1.py
```

아래 코드에서 **캘리브레이션 파일 경로를 실제 경로로 수정**합니다.

```python
with open('your/path/to/camera_calibration.pkl', 'rb') as f:
```

예시:

```python
with open('/home/pi/colcon_ws/src/csi_cam/calibration/camera_calibration.pkl', 'rb') as f:
```

---

### 7️⃣ ROS 2 CSI 카메라 노드 실행

```bash
ros2 run csi_cam cam1
```

퍼블리시되는 토픽 확인:

```bash
ros2 topic list
```

영상 확인:

```bash
rqt
```

✔ 캘리브레이션은 **카메라 변경 시, 해상도 변경 시, 렌즈 특성이 다른 경우** 다시 수행하는 것을 권장합니다.

---

## 📡 ROS 2 토픽

퍼블리시되는 주요 토픽 예시:

* `/csi_cam/image_raw`
* `/csi_cam/compressed`

메시지 타입:

* `sensor_msgs/msg/Image`
* `sensor_msgs/msg/CompressedImage`

---

## 📝 참고 사항

* CSI 카메라는 부팅 전에 반드시 연결되어 있어야 합니다.
* `rpicam-still`이 정상 동작하는지 확인한 후 ROS 2 노드를 실행하세요.
* 본 프로젝트는 **Raspberry Pi 5 + Ubuntu 24.04 + ROS 2 Jazzy** 환경을 기준으로 작성되었습니다.

---

## 📄 라이선스

본 프로젝트는 사용된 각 오픈소스 저장소의 라이선스를 따릅니다.
