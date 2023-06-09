#! /bin/bash

xhost +local:docker
export XSOCK=/tmp/.X11-unix
export XAUTH=/tmp/.docker.xauth
xauth nlist $DISPLAY | sed -e 's/^..../ffff/' | xauth -f $XAUTH nmerge -
export lock_id="${1}"
export verification_service_url="http://verification:5000"
docker compose -f docker-compose.edge.laptop.yaml up --build