import sys
from random import randint

# print "What is your name?"
# name = sys.stdin.readline()
# print "Hello " + name

while True:
	x = randint(1,5)
	y = randint(1,5)
	answer = -1
	print "What is " + str(x) + "+" + str(y) + "?"
	answer = sys.stdin.readline()
	try:
		if (int)(answer.strip()) == x+y:
			print "Correct!"
		else:
			print "Sorry, that's not right!"
	except ValueError:
		print "That's not a number!"