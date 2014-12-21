#!/usr/bin/env python

import sys
from dateutil import parser
from datetime import timedelta

delta = int(sys.argv[1])

#take a line from stdin, interpret it as a date, and add delta days to it
for line in sys.stdin:
	initial_date = parser.parse(line.strip())
	final_date = initial_date + timedelta(delta)
	sys.stdout.write(final_date.strftime('%m/%d/%y') + '\n')
