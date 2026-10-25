# 실차 중간평가 로직과 동기화한 시뮬레이션 — 2026-10-25

`fix/midterm`은 실차 저장소의 커밋 `ee56def`에 있는 주행 로직·모델·파라미터를 반영한다.
실차 저장소의 소스와 하드웨어 설정은 변경하지 않는다.
Gazebo 월드·차량 로딩·카메라 토픽·시뮬레이터 명령 전송 코드는 기존 시뮬레이션 구성을 유지한다.

`src/simulation_pkg/launch/driving_sim.launch.py`와 `mission_sim.launch.py`에 동일하게 적용했다.

| 파라미터 | 값 | 의미 |
|---|---|---|
| lane_target_ratio | 0.6 | 인식된 좌우 경계 사이의 목표 위치. 0.5는 중앙, 클수록 오른쪽 |
| driving_speed | 255 | 정상 주행 명령 |
| lane_loss_speed | 220 | lane2 미검출 중 주행 명령 |
| lane_detection_timeout | 0.2 | 인식/유효 경로 갱신이 끊겼을 때 감속 기준 시간(초) |
| kp_heading | 0.09 | 경로 방향 오차에 대한 조향 게인 |
| steering_alpha | 0.4 | 조향 EMA 계수 |
| max_steering_step | 4.0 | 제어 주기당 조향 변화량 제한 |
| timer | 0.05 | 제어 주기(초), 20 Hz |

공유 코드: YOLO, lane2 마스크/목표점 추출, 경로 생성, 조향/속도 제어,
신호등 색상 검출, 주행 경로 시각화. YOLO는 `cuda:0`, FP32 추론을 사용한다.
일반 검출 임계값은 0.3, lane2 임계값은 0.15다.

첫 유효 경로가 들어오기 전에는 정지한다. 경로를 한 번 받으면 출발 허용 상태를 유지한다.
주행 중 lane2 미검출 메시지를 받으면 즉시 220으로 감속하고 마지막 경로를 유지한다.
0.2초는 미검출 메시지의 유예 시간이 아니라 인식/경로 갱신 중단을 판단하는 시간이다.
LiDAR 장애물 입력에 의한 정지는 활성 상태다. 빨간 신호등 정지의
`should_stop = True` 줄은 실차와 같이 주석 처리되어 있다.
따라서 `mission_sim`에 신호등을 생성해도 현재 제어기는 빨간불만으로 정지하지 않는다.
정지 사유와 해제 시간은 `STOP`, `STOP_END` 로그에 기록한다.

기본 모델: `model/v3.2_finetuned_corner4_with_v3.pt`.
SHA256: `b34cb3d8e6633d873f982a73c12d46090c5260e145b780bc9383ad2e09067f86`.
`model/best.pt`와 `src/simulation_pkg/simulation_pkg/data/sim.pt`도 동일한 가중치다.
모델 v3/v3.1/v3.2를 모두 보존하며, 비교 방법은 `MODEL_COMPARE_2026-10-16.md`를 참고한다.
모델 경로는 각 저장소 내부를 가리키므로 시뮬레이션만 clone해도 가중치를 사용할 수 있다.

최초 설치 또는 새 clone 후 빌드:

```bash
cd /home/autolab/ros2_autonomous_vehicle_simulation
source /opt/ros/humble/setup.bash
colcon build --symlink-install
```

Gazebo와 ROS 노드를 이 PC에서 함께 실행하는 구성:

```bash
ROS_LOCALHOST_ONLY=1 /home/autolab/ros2_autonomous_vehicle_simulation/run_driving_sim.sh
```

모델만 바꾸어 비교:

```bash
ROS_LOCALHOST_ONLY=1 /home/autolab/ros2_autonomous_vehicle_simulation/run_model_compare.sh v3.2
```

미션 월드 실행:

```bash
cd /home/autolab/ros2_autonomous_vehicle_simulation
source /opt/ros/humble/setup.bash
source install/local_setup.bash
ROS_LOCALHOST_ONLY=1 ros2 launch simulation_pkg mission_sim.launch.py
```

`ROS_LOCALHOST_ONLY=1`은 네트워크의 다른 ROS 실행과 토픽이 섞이지 않도록
위 명령에 지정한다. runner가 환경 변수를 강제하지는 않는다.
현재 symlink 설치는 소스 수정 후 재시작으로 반영되며 새 clone에서는 먼저 빌드해야 한다.
이번 동기화의 검증은 제어 동작 테스트와 launch/모델/공유 코드 일치 확인으로 수행한다.
실차 구동이나 Arduino 업로드를 실행하지 않는다.
