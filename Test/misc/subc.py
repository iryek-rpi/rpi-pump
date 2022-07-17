
class C1():
  def __init__(self, execute, *args, **kwargs):
    self.execute = execute
    self.args = args
    self.kwargs = kwargs
      
  def run(self):
    print("C1:self.execute:", self.execute)
            
class C2(C1):
  def __init__(self, execute, *args, **kwargs):
    pass
      
  def run(self):
    print("C2: self.execute:", self.execute)