#!/bin/sh

if [ "$USE_HOST_NETWORK" = "true" ]; then
    echo "Using Host Network: Replacing service names with 127.0.0.1"
    sed -i 's/frontend:3000/127.0.0.1:3000/g' /etc/nginx/conf.d/default.conf
    sed -i 's/backend:8000/127.0.0.1:8000/g' /etc/nginx/conf.d/default.conf
fi

# Execute the CMD (nginx)
exec "$@"
