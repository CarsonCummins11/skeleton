#!/bin/bash

SERVICE_NAME="thing"

echo "Stopping and removing all containers for service: $SERVICE_NAME"
docker ps -a --filter "name=$SERVICE_NAME" --format "{{.ID}}" | xargs -r docker rm -f

echo "Removing images for service: $SERVICE_NAME"
docker images --format "{{.ID}} {{.Repository}}" | awk -v service="$SERVICE_NAME" '$2 ~ service {print $1}' | xargs -r docker rmi -f

echo "Removing volumes associated with service: $SERVICE_NAME"
docker volume ls --format "{{.Name}}" | grep "$SERVICE_NAME" | xargs -r docker volume rm -f

echo "Pruning unused images, volumes, and build cache"
docker system prune -af

echo "Cleanup complete."

docker compose up