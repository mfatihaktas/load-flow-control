#!/bin/bash
echo $1 $2 $3

PY=python3

if [ $1 = 'n' ]; then
  sudo $PY net.py
elif [ $1 = 'c' ]; then
  # [ -z "$2" ] && { echo "Which controller [0, *] ?"; exit 1; }
  $PY comm.py --ip_l=10.0.0.1,10.0.0.2
elif [ $1 = 'e' ]; then
  $PY edge_cloud.py --ip_l=10.0.0.1,10.0.0.2
else
  echo "Arg did not match!"
fi
