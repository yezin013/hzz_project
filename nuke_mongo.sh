#!/bin/bash
set -x
sudo docker rm -f mongodb || true
sudo killall -9 mongod || true
sudo pkill -f mongod || true
sleep 2
if sudo lsof -i :27017; then
    echo "Port 27017 still in use! Force killing PIDs..."
    sudo lsof -t -i :27017 | xargs sudo kill -9
fi
echo "Cleanup complete."
