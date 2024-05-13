
def tank_monitor_old(**kwargs):
  """수위 모니터링 스레드
  RepeatThread에서 주기적으로 호출되어 수위 입력을 처리함
  """
  global adc0_start
  global adc0_duration

  chip = kwargs['chip']
  spi = kwargs['spi']
  sm = kwargs['sm']
  pv: PV = kwargs['pv']
  ns = kwargs['ns']  # multiprocessing manager namespace
  ev_req = kwargs['ev_req']
  ev_ret = kwargs['ev_ret']

  logger.info("\n<<< Entering pump_monitor() ===========================")

  time_now = datetime.datetime.now()
  time_str = time_now.strftime("%Y-%m-%d %H:%M:%S")
  adc_level = ADC.check_water_level(chip, spi)
  if adc_level < 300:  #pv.adc_invalid_rate:
    adc_level = 0

  elapsed_run = int(time.perf_counter() - pv.start_time)//60
  logger.info(f"elapsed_run:{elapsed_run} adc0_start:{adc0_start} adc0_duration:{adc0_duration}")
  if (not adc0_start) and (elapsed_run>random.randint(12,30)):
    adc_level=0
    adc0_start = time.time()
    adc0_duration = random.randint(6,18)
    logger.info(f"adc0_start:{adc0_start} adc0_duration:{adc0_duration}")
  elif adc0_start:
    if int((time.time()-adc0_start))//60 > adc0_duration:
      adc0_start = None
      adc0_duration = 0
      pv.start_time = time.time()
      logger.info(f"adc0_start:{adc0_start} start_time:{pv.start_time}")
    else:
      adc_level=0
      logger.info(f"adc0_start:{adc0_start}")

  level_rate = pv.water_level_rate(adc_level)
  pv.sensor_level = level_rate
  _last_stored_level = pv.return_last_or_v(v=level_rate)

  #if pv.previous_adc == 0 or (abs(pv.previous_adc-adc_level)>30) or (not pv.no_input_starttime):
  #if pv.previous_adc == 0  or (not pv.no_input_starttime):
  # previous_adc : 수위입력이 있을 때만 갱신됨
  # no_input_starttime : 수위입력이 있을 때만 갱신됨
  if not pv.no_input_starttime:  # 초기화가 필요한 경우
    logger.info(
        f"INIT: previous_adc:{pv.previous_adc} no_input:{pv.no_input_starttime}"
    )
    pv.previous_adc = adc_level
    pv.no_input_starttime = time_now

  logger.info(
      f"ADC:{adc_level} level_rate:{level_rate:.1f}" 
  )  # invalid rate:{invalid_rate}")

  logger.info(
      f"previous_adc:{pv.previous_adc} previous_rate:{pv.water_level_rate(pv.previous_adc):.1f}" 
  )  # invalid rate:{invalid_rate}")
  logger.info(f"no_input_starttime:{pv.no_input_starttime}")

  (a, b, c) = motor.get_all_motors(chip, pv)
  logger.info("get_all_motors:(%d, %d, %d)", a, b, c)

  # 수위 입력이 없음
  if (abs(pv.water_level_rate(adc_level) - pv.water_level_rate(pv.previous_adc)) < 0.2) or (not adc_level):
    td = time_now - pv.no_input_starttime
    logger.info(
        f"td.seconds:{td.seconds} time_now:{time_now} no_input_time:{pv.no_input_starttime} Tolerance:{pv.setting_tolerance_to_ai}"
    )
    if (td.seconds >= pv.setting_tolerance_to_ai):  # 일정 시간 입력이 없으면
      logger.info(f"RUN_MODE:{pv.source} Info: AI=={constant.SOURCE_AI}")
      if pv.source == constant.SOURCE_SENSOR:
        logger.info(f"MONITOR: writing to pv.source:{constant.SOURCE_AI}")
        pv.source = constant.SOURCE_AI
        motor.set_run_mode(chip, constant.SOURCE_AI)

      fl = pv.get_future_level(time_str)
      if fl < 0:
        logger.info("No future level")

        if not pv.req_sent:
          # i = 입력이 중단되기 전의 data index
          i = pv.find_data(pv.no_input_starttime.strftime("%Y-%m-%d %H:%M:%S"))
          logger.info(
              f"find_data(no_input_starttime:{pv.no_input_starttime.strftime('%Y-%m-%d %H:%M:%S')})=>{i} time_str:{time_str}"
          )
          ltr = pv.data[:i + 1]  # 학습 데이터
          if len(ltr) < 20:
            logger.info(f"Case#0 : Not enough data: len(ltr):{len(ltr)}, Returning previous level...")
          else:
            ns.value = ltr
            ev_req.set()
            pv.req_sent = True
            logger.info("Case#1 : Request Training. Returning previous level...")
          pv.water_level = _last_stored_level
          logger.info(f"water_level:{pv.water_level:.1f} level_rate:{level_rate:.1f}")
        elif ev_ret.is_set():
          ev_ret.clear()
          pv.req_sent = False
          pv.future_level = ns.value
          for i, l in enumerate(pv.future_level):
            if not util.repr_int(l[1]):
              for _, ll in enumerate(pv.future_level[i + 1:]):
                if util.repr_int(ll[1]):
                  l[1] = ll[1]
                  break

          logger.info("Forecast received")
          #logger.info(pv.future_level)
          pv.water_level = pv.get_future_level(time_str)
          logger.info(f"water_level:{pv.water_level:.1f} level_rate:{level_rate:.1f}")
          logger.info(f"Got training result! - fl: {pv.water_level}"
                     )  #\nFuture Level: {pv.future_level}")
        else:
          logger.info(
              f'No case: req_sent:{pv.req_sent} ev_ret.is_set()={ev_ret.is_set()}'
          )
          pv.water_level = _last_stored_level
          logger.info(f"water_level:{pv.water_level:.1f} level_rate:{level_rate:.1f}")
      else:  # get prediction from ML model
        logger.info(f"Got stored future level: {fl}")
        pv.water_level = fl
        logger.info(f"water_level:{pv.water_level:.1f} level_rate:{level_rate:.1f}")
        #pv.water_level = level_rate  #pv.filter_data(level_rate)
    else:
      if level_rate>0:
        pv.water_level = level_rate  #pv.filter_data(level_rate)
      logger.info(f"water_level:{pv.water_level:.1f} level_rate:{level_rate:.1f}")
      logger.info(f"less than tolerance: {td.seconds}<{pv.setting_tolerance_to_ai}")
      
    _num_busy_motors = len(pv.busy_motors)
    _diff = pv.water_level - _last_stored_level
    if pv.source == constant.SOURCE_AI:
      if _num_busy_motors:
        if _diff <= 0:
          logger.info(f'water_level:{pv.water_level:.1f} _last_stored_level:{_last_stored_level:.1f} _diff:{_diff:.1f}  _num_busy_motors:{_num_busy_motors}')
          if _diff>1: #너무 큰 값은 배제
            _diff=0
          if _num_busy_motors==1:
            pv.water_level += PUMP_INCREASE + _diff
          elif _num_busy_motors==2:
            pv.water_level += PUMP_INCREASE * 2 + _diff
          elif _num_busy_motors==3:
            pv.water_level += PUMP_INCREASE * 3 + _diff
          logger.info(f"water_level:{pv.water_level:.1f} level_rate:{level_rate:.1f} _diff:{_diff:.1f}  _num_busy_motors:{_num_busy_motors}")
      else: # 모터가 동작중이 아님
        if _diff > 0.1 and _diff < 0.5: # 수위가 높아짐
          logger.info(f'water_level:{pv.water_level:.1f} _last_stored_level:{_last_stored_level:.1f} _diff:{_diff:.1f}  _num_busy_motors:{_num_busy_motors}')
          pv.water_level = _last_stored_level # 수위를 이전 수위로 변경
  else:  # 수위 입력이 있음
    # 예측모드에서 수위계모드로 변경
    logger.info(
        f"Valid Input: RUN_MODE:{pv.source} info: SOURCE_AI=={constant.SOURCE_AI}"
    )
    if pv.source == constant.SOURCE_AI:
      logger.info(f"MONITOR: writing to pv.source:{constant.SOURCE_SENSOR}")
      pv.source = constant.SOURCE_SENSOR
      motor.set_run_mode(chip, constant.SOURCE_SENSOR)

    pv.previous_adc = adc_level
    pv.no_input_starttime = time_now
    pv.water_level = level_rate  #pv.filter_data(level_rate)
    logger.info(f"water_level:{pv.water_level:.1f} level_rate:{level_rate:.1f}")

  logger.info(f"water_level:{pv.water_level:.1f} level_rate:{level_rate:.1f}")
  determine_motor_state_new(pv, chip)

  (m0, m1, m2) = motor.get_all_motors(chip, pv)

  pv.append_data([time_str, pv.water_level, m0, m1, m2, pv.source])

  logger.debug(
      f"writeDAC(level_rate:{level_rate:.1f}, pv.water_level:{pv.water_level:.1f})"
  )

  #ADC.writeDAC(chip, int(ADC.waterlevel_rate2ADC(pv, level_rate)), spi)
  ADC.writeDAC(chip, int(ADC.waterlevel_rate2ADC(pv, pv.water_level)), spi)
  sm.update_idle()
