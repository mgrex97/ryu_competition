#!/bin/bash
for i in `seq 1 $2`
do
    date="`date +%T`"
    echo "$i : $date" | netcat -w 1 -u $1 5000;
#    sleep 0.5;
done
