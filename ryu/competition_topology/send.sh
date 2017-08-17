#!/bin/bash
mkdir -p /dev/udp
index=0
while true;
do
    ((index++));
    date="`date +%T`"
    echo "Antslab $index : $date" > /dev/udp/$1/5000
    #hping3 $1 -2 -e "Antslab $index : $date" -p 5000 -c 1
    sleep 1;
done
