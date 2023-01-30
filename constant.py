# PUMP 갯수
PUMP_COUNT = 3

# 수위계 입력에 의한 수위값인지, 예측에 의한 수위값인지
SOURCE_SENSOR = 0
SOURCE_AI = 1

# 펌프 가동을 자동으로 할 지 여부
PUMP_MODE_MANUAL = 0
PUMP_MODE_AUTO = 1

# PLC와 연동해서 동작할 지, 단독으로 동작할 지
MODE_PLC = 0  # PLC에서 pump control
MODE_SOLO = 1  # 수위조절기에서 pump control

MAX_TRAIN_SAMPLES = 3600 * 6
MAX_PREDICT_SAMPLES = 3600 * 24 