import datetime

SOURCE = 0
WATER_LEVEL = 0
PREVIOUS_ADC = 0
NO_INPUT_START = None
data = []


def tank_monitor(adc):
  global SOURCE
  global WATER_LEVEL
  global PREVIOUS_ADC
  global NO_INPUT_START

  time_now = datetime.datetime.now()
  adc_level = adc
  if adc_level < 100:
    adc_level = 0

  if NO_INPUT_START:
    print(
        f"\n0 adc:{adc_level} PREVIOUS:{PREVIOUS_ADC} NO_INPUT:{NO_INPUT_START.strftime('%D:%M:%S')} SOURCE:{SOURCE} WATER_LEVEL:{WATER_LEVEL}"
    )
  else:
    print(
        f"\n0 adc:{adc_level} PREVIOUS:{PREVIOUS_ADC} NO_INPUT:{NO_INPUT_START} SOURCE:{SOURCE} WATER_LEVEL:{WATER_LEVEL}"
    )
  #  level_rate = pv.WATER_LEVEL_rate(adc_level)
  orig_level = adc_level  #pv.WATER_LEVEL

  if not (PREVIOUS_ADC and NO_INPUT_START):  # 초기화가 필요한 경우
    PREVIOUS_ADC = adc_level
    NO_INPUT_START = time_now

  print(
      f"1 adc:{adc_level} PREVIOUS:{PREVIOUS_ADC} NO_INPUT:{NO_INPUT_START.strftime('%D:%M:%S')} SOURCE:{SOURCE} WATER_LEVEL:{WATER_LEVEL}"
  )
  # 수위 입력이 없음
  if abs(adc_level - PREVIOUS_ADC) < 30:
    td = time_now - NO_INPUT_START
    print(f"NO INPUT 0: td.seconds:{td.seconds} Tolerance:{30}")
    if (td.seconds >= 30):  # 일정 시간 입력이 없으면
      print(f"NO INPUT 1: td.seconds:{td.seconds} Tolerance:{30}")
      print(f"RUN_MODE:{SOURCE}")
      if SOURCE == 0:
        SOURCE = 1
      if len(data) > 5:
        WATER_LEVEL = adc_level + 10000
        print(f"##### Predicted level: {WATER_LEVEL}")
      else:
        print("###### Training failed. returning original value")
        WATER_LEVEL = orig_level
      # get prediction from ML model
      print(f"2 SOURCE:{SOURCE} WATER_LEVEL:{WATER_LEVEL}")

    else:
      print(f"NO INPUT 2: td.seconds:{td.seconds} Tolerance:{30}")
      WATER_LEVEL = orig_level  # 일시적인 현상으로 간주하고 level 값 버림
      print(f"3 SOURCE:{SOURCE} WATER_LEVEL:{WATER_LEVEL}")
  else:  # 수위 입력이 있음
    # 예측모드에서 수위계모드로 변경
    print(f"RUN_MODE:{SOURCE}")
    if SOURCE == 1:
      SOURCE = 0
      print(f"4 SOURCE:{SOURCE} WATER_LEVEL:{WATER_LEVEL}")

    PREVIOUS_ADC = adc_level
    NO_INPUT_START = time_now
    WATER_LEVEL = adc_level

  append_data([time_now.strftime("%Y-%m-%d %H:%M:%S"), WATER_LEVEL, SOURCE])
  print(
      f"5 adc:{adc_level} PREVIOUS:{PREVIOUS_ADC} NO_INPUT:{NO_INPUT_START.strftime('%D:%M:%S')} SOURCE:{SOURCE} WATER_LEVEL:{WATER_LEVEL}"
  )


def append_data(l):
  data.append(l)