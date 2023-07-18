import time

def seconds():
	second = input("Number of seconds = ")
	for x in range(int(second)):
		print ("Hello")
		time.sleep(1)
seconds()