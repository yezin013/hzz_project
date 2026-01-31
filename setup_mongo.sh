#!/bin/bash
set -e

# Setup MongoDB Node
set -e

# Ensure Docker is installed
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
fi

# Stop existing container
sudo docker rm -f mongodb || true

# Setup directories
sudo mkdir -p /etc/mongo-keyfile
sudo mkdir -p /data/db

# Move keyfile to correct location and strip CRLF
if [ -f /home/ubuntu/mongo-keyfile ]; then
    # Critical: remove Windows carriage returns
    tr -d '\r' < /home/ubuntu/mongo-keyfile | sudo tee /etc/mongo-keyfile/mongo-keyfile > /dev/null
    rm /home/ubuntu/mongo-keyfile
fi

# Set permissions
sudo chmod 400 /etc/mongo-keyfile/mongo-keyfile
sudo chown 999:999 /etc/mongo-keyfile/mongo-keyfile
sudo chown -R 999:999 /data/db

# Run MongoDB
sudo docker run -d \
  --net=host \
  --restart always \
  --name mongodb \
  -v /etc/mongo-keyfile:/etc/mongo-keyfile \
  -v /data/db:/data/db \
  mongo:7.0 \
  --replSet my-replica-set \
  --keyFile /etc/mongo-keyfile/mongo-keyfile \
  --bind_ip_all

echo "MongoDB started successfully."
