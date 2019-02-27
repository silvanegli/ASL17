#!/bin/bash

source ./functions.sh

if check_if_machines_down "mw1" "mw2"; then
	./startVms.sh asl4 asl5
fi

echo "building middleware with latest gitlab changes"
#git add ../src/*.java
#git commit -m "java debug"
#git push origin master
ssh siegli@mw1 "cd asl-17 && git pull origin master && ant clean compile jar && cd -" &
ssh siegli@mw2 "cd asl-17 && git pull origin master && ant clean compile jar && cd -" &

wait_for_jobs
#./stopVms.sh aslvm4 aslvm5
