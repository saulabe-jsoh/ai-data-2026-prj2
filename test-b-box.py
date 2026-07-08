# install (python -m)
# !pip install ultralytics opencv-python-headless matplotlib

# code
import cv2
import numpy as np
import matplotlib.pyplot as plt
from ultralytics import YOLO
from base64 import b64encode

# ==============================================================================
# [준비 단계] 테스트용 가상 비행 물체 영상(MP4) 생성
# ==============================================================================
print("1. 테스트용 가상 비행 물체 영상을 생성하는 중...")
width, height = 640, 480
fps = 30
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out_video = cv2.VideoWriter('test_input.mp4', fourcc, fps, (width, height))

# 10초 동안 대각선으로 불규칙하게 움직이는 가상 객체 프레임 기록
bird_x, bird_y = 50, 50
dx, dy = 4, 3

for frame_idx in range(300): # 300 프레임 = 10초
    # 배경은 밤하늘(어두운 회색)
    frame = np.ones((height, width, 3), dtype=np.uint8) * 20
    
    # 난기류 및 불규칙 비행 모사를 위한 약간의 무작위 흔들림 추가
    if frame_idx % 15 == 0:
        dx += np.random.randint(-2, 3)
        dy += np.random.randint(-2, 3)
    
    bird_x = (bird_x + dx) % width
    bird_y = (bird_y + dy) % height
    
    # 레이더/EOIR에 포착된 붉은색 비행 물체(새 떼) 그리기
    cv2.circle(frame, (int(bird_x), int(bird_y)), 12, (0, 0, 255), -1)
    out_video.write(frame)

out_video.release()
print("▶ 'test_input.mp4' 비행 영상 생성 완료!\n")


# ==============================================================================
# [핵심 단계] 영상 속 오브젝트를 탐지하고 사각형 가이드(바운딩 박스) 그리기
# ==============================================================================
print("2. AI 객체 탐지 및 사각형 가이드(Bounding Box) 프로세스 가동...")

# 가볍고 빠른 초경량 탐지 모델(YOLOv8-nano) 로드
model = YOLO('yolov8n.pt') 

# 비행 영상 다시 읽기
cap = cv2.VideoCapture('test_input.mp4')
output_fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out_processed = cv2.VideoWriter('processed_output.mp4', output_fourcc, fps, (width, height))

frame_count = 0
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
        
    # AI 모델을 통해 현재 프레임 속 모든 오브젝트(물체)의 좌표 검출
    # 실제 환경에서는 조류(bird) 혹은 항공기(aeroplane) 클래스 필터링 적용 가능
    results = model(frame, verbose=False)
    
    # 검출된 오브젝트들의 정보 가져오기
    for result in results:
        boxes = result.boxes
        for box in boxes:
            # 1) 사각형 가이드 박스의 좌상단(x1, y1) 및 우하단(x2, y2) 픽셀 좌표 역산
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            
            # 2) 신뢰도 점수(Confidence Score) 추출 (예: 0.85 = 85% 확신)
            conf = float(box.conf[0])
            
            # 3) 물체의 종류(Class ID) 추출
            cls = int(box.cls[0])
            label = f"Target: {conf:.2f}"
            
            # 4) OpenCV를 이용해 영상 프레임 위에 사각형 가이드 라인 칠하기
            # cv2.rectangle(이미지, 좌상단좌표, 우하단좌표, 색상(BGR), 선두께)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # 5) 사각형 상단에 타겟 정보 텍스트 표기
            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # 6) 화면 정중앙(조준선 십자 가이드)과 표적 중심 간의 오차 파악용 가이드선 그리기
            obj_center_x = (x1 + x2) // 2
            obj_center_y = (y1 + y2) // 2
            cv2.line(frame, (320, 240), (obj_center_x, obj_center_y), (255, 255, 0), 1)

    # 처리된 프레임을 결과 영상 파일에 기록
    out_processed.write(frame)
    frame_count += 1

cap.release()
out_processed.write(frame)
out_processed.release()
print(f"▶ 총 {frame_count} 프레임 영상 분석 및 사각형 가이드 매핑 완료!\n")


# ==============================================================================
# [시각화 단계] 코랩 환경에서 HTML5 비디오 플레이어로 처리된 영상 확인하기
# ==============================================================================
print("3. 분석 완료된 최종 영상을 웹 브라우저 플레이어로 인코딩합니다...")

# 코랩 브라우저 재생용 코덱 변환 (H.264 인코딩)
# how to install.
# !ffmpeg -y -i processed_output.mp4 -vcodec libx264 -f mp4 converted_final.mp4 -loglevel quiet

from IPython.display import HTML

# HTML 비디오 태그 출력
mp4 = open('converted_final.mp4', 'rb').read()
data_url = "data:video/mp4;base64," + b64encode(mp4).decode()
HTML(f"""
<div style="text-align:center;">
    <h3>🦅 실시간 AVT 사각형 가이드 시뮬레이션 결과</h3>
    <video width="640" height="480" controls autoplay loop>
        <source src="{data_url}" type="video/mp4">
    </video>
    <p style="color:#7f8c8d; font-size:13px;">초록색 사각형: AI가 검출한 물체 바운딩 박스 / 하늘색 선: 화면 중심과 물체 간의 거리 오차(Δ)</p>
</div>
""")
