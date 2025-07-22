import threading

# def thread(func, args):
# 	try:
# 		th = threading.Thread(target=func, args=args)
# 		th.start()
# 		threading.main_thread()
# 		# th.join()
# 	except Exception as e:
# 		print("Error in thread")
# 		print(e)
	
# def stop(name=""):
# 	print("Threads:")
# 	for t in threading.enumerate():
# 		print("  ", t.getName())
# 		if t.getName() == str(name):
# 			print("Stopping...")
# 			t.do_run = False
# 			t.join()

# def show():
# 	print("Threads:")
# 	for t in threading.enumerate():
# 		print("  ", t.getName())
# 	print()




class Threads():
	"""docstring for Threads"""
	def __init__(self):
		self.__threads = []
		self.__rlock = threading.RLock()

	def rlock(self):
		return self.__rlock

	def run(self, func, args):
		th = threading.Thread(target=func, args=args)
		self.__threads.append(th)
		th.start()
		
	def show(self):
		print("Threads:")
		for t in threading.enumerate():
			print("  ", t.getName())
		print()

	def stop(self, name=""):
		print("Threads:")
		for t in threading.enumerate():
			print("  ", t.getName())
			if t.getName() == str(name):
				print("Stopping...")
				t.do_run = False
				t.join()

	def stopAll(self):
		for t in self.__threads:
			print(t.getName())
			t.do_run = False
			t.join()

	def threads(self):
		response_text = ""
		for thread in threading.enumerate():
			response_text += f"{thread.getName()}\r\n"

		if response_text:
			return response_text
		return "-"