cp /usr/lib/python3/dist-packages/gpiozero/pins/lgpio.py .

* gpiozero v1.62 기준 pin factory로 lgpio를 사용하기 위해서는 'lgpio.py'를 수정해야함
{{{
lgpio.gpio_claim_input(
  self.factory._handle, self.number, 0) #lgpio.SET_BIAS_DISABLE)

  flags = {
    'up': lgpio.SET_PULL_UP, #lgpio.SET_BIAS_PULL_UP,
    'down': lgpio.SET_PULL_DOWN, #lgpio.SET_BIAS_PULL_DOWN,
    'floating': 0, #lgpio.SET_BIAS_DISABLE,
  }[value]

lgpio.SET_BIAS_XXX를 모두 lgpio.SET_XXX로 수정
lgpio.SET_BIAS_DISABLE -> 0으로 수정
}}}
