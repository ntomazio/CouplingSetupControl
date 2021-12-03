import controller

task = controller.Task()
task.add_channel("Dev1/ai0")
task.add_channel("Dev1/ai3")
task.config()
r = task.read()
task.close() 