import cv2
import numpy as np
import os
import glob
import pickle
import datetime
import subprocess
import shlex

def capture_camera():
    # 카메라 장치 열기
    cmd = 'rpicam-vid --inline --nopreview -t 0 --codec mjpeg --width 640 --height 480 --framerate 30 -o - --camera 0'
    process = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    buffer = b""
    delay = 0
    i = 0
    while True:
        buffer += process.stdout.read(4096)
        a = buffer.find(b'\xff\xd8')
        b = buffer.find(b'\xff\xd9')

        if a != -1 and b != -1:
            jpg = buffer[a:b+2]
            buffer = buffer[b+2:]

            frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)

            # 파일 이름에 현재 날짜와 시간을 추가하여 저장
            if delay >= 25:
                i += 1
                filename = f"./checkerboards/capture_{i}.png"
                cv2.imwrite(filename, frame)
                print(f"{filename} 이미지가 저장되었습니다.")
                delay = 0
            delay += 1
            frame = cv2.flip(frame, -1)
            # 프레임을 화면에 표시
            cv2.imshow("Video", frame)
            # 'q' 키를 누르면 종료
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cv2.destroyAllWindows()

def calibrate_camera():
    # 체커보드의 차원 정의
    CHECKERBOARD = (7,10)  # 체커보드 행과 열당 내부 코너 수
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    
    # 각 체커보드 이미지에 대한 3D 점 벡터를 저장할 벡터 생성
    objpoints = []
    # 각 체커보드 이미지에 대한 2D 점 벡터를 저장할 벡터 생성
    imgpoints = [] 
    
    # 3D 점의 세계 좌표 정의
    objp = np.zeros((1, CHECKERBOARD[0] * CHECKERBOARD[1], 3), np.float32)
    objp[0,:,:2] = np.mgrid[0:CHECKERBOARD[0], 0:CHECKERBOARD[1]].T.reshape(-1, 2) * 22 # lengt of squre(mm)
    
    # 주어진 디렉터리에 저장된 개별 이미지의 경로 추출
    images = glob.glob('./checkerboards/*.png')
    
    for fname in images:
        img = cv2.imread(fname)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 체커보드 코너 찾기
        ret, corners = cv2.findChessboardCorners(gray,
                                               CHECKERBOARD,
                                               cv2.CALIB_CB_ADAPTIVE_THRESH +
                                               cv2.CALIB_CB_FAST_CHECK +
                                               cv2.CALIB_CB_NORMALIZE_IMAGE)
        
        if ret == True:
            objpoints.append(objp)
            corners2 = cv2.cornerSubPix(gray, corners, (11,11), (-1,-1), criteria)
            imgpoints.append(corners2)
            
            # 코너 그리기 및 표시
            img = cv2.drawChessboardCorners(img, CHECKERBOARD, corners2, ret)
            cv2.imshow('img', img)
            cv2.waitKey(100)
    
    cv2.destroyAllWindows()
    
    # 카메라 캘리브레이션 수행
    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)
    
    # 결과 출력
    print("Camera matrix : \n")
    print(mtx)
    print("\ndist : \n")
    print(dist)
    print("\nrvecs : \n")
    print(rvecs)
    print("\ntvecs : \n")
    print(tvecs)
    
    # 캘리브레이션 결과를 파일로 저장
    calibration_data = {
        'camera_matrix': mtx,
        'dist_coeffs': dist,
        'rvecs': rvecs,
        'tvecs': tvecs
    }
    
    with open('camera_calibration.pkl', 'wb') as f:
        pickle.dump(calibration_data, f)

if __name__ == "__main__":
    print("Caputur&Save Camera")
    capture_camera()
    print("Performing new camera calibration...")
    calibrate_camera()
