#! /bin/bash

xhost +local:docker
export XSOCK=/tmp/.X11-unix
export XAUTH=/tmp/.docker.xauth
xauth nlist $DISPLAY | sed -e 's/^..../ffff/' | xauth -f $XAUTH nmerge -