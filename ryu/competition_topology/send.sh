#!/bin/bash
index=0
while true;
do
    ((index++));
    date="`date +%T`"
    echo "$index : $date"  | nc -u -q 1 -p 5001 $1 5000
done
