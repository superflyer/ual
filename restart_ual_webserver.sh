kill `ps -f -u root | grep 'ual_webserver' | grep -v grep | egrep -o 'root +[0-9]+' | egrep -o '[0-9]+'`
nohup src/ual_webserver.py -c /root/ual.config -p 4321 1>> logs/webserver.log 2>> logs/webserver.err &

