#!/bin/bash

# Stop the Docker containers
docker compose down


# Remove the existing SQL Docker volume
docker volume rm $(docker volume ls -qf "name=db")

# Remove the existing Redis Docker volume
docker volume rm $(docker volume ls -qf "name=redis")

# Start the Docker containers
docker compose up