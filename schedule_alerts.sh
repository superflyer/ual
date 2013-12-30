while :
do
	./ual.py 1>> alerts.out 2>> alerts.err
	sleep ${1}h
done
