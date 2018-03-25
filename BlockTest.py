import fcntl
import os
import sys

# make stdin a non-blocking file
fd = sys.stdin.fileno()
fl = fcntl.fcntl(fd, fcntl.F_GETFL)
fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

def testIn(input):
	if input != "":
		print("Hi")
		exit(0)
	else:
		print("No")

# user input handling thread
while (True):
	testIn(sys.stdin.readline())