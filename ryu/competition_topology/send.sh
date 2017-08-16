#!/bin/bash
mkdir -p /dev/udp

for i in `seq 1 $2`
do
    date="`date +%T`"
    echo "Antslab $i : $date" > /dev/udp/$1/5000
    sleep 1;
done
