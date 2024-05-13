setting_4ma_ref = 700
setting_20ma_ref = 4000


def rate2ADC(rate):
  if rate <= 0:
    v = setting_4ma_ref
  elif rate >= 100:
    v = setting_20ma_ref
  else:
    v = setting_4ma_ref + (rate / 100) * (setting_20ma_ref - setting_4ma_ref)

  return v


def percent(adc):
  rate = 0.0
  if adc >= setting_20ma_ref:
    rate = 100.0
  elif adc < setting_4ma_ref:
    rate = 0.0
  else:
    rate = ((adc - setting_4ma_ref) /
            (setting_20ma_ref - setting_4ma_ref)) * 100.0
  return rate