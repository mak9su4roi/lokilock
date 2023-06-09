#! /bin/bash

export lock_id="${1}"
export verification_service_url="${2}"

docker compose -f docker-compose.edge.rpi4.yaml up --build