#!/bin/bash
mkdir -p /dev/udp
index=0
while true;
do
    ((index++));
    date="`date +%T`"
    echo "Antslab $index : $date" > /dev/udp/$1/5000
    sleep 1;
done
