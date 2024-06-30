#!/bin/sh
# # Set number of workers based on logical CPU cores
# export WORKERS=$(grep -c ^processor /proc/cpuinfo)

# echo "Starting server with $WORKERS workers"

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
