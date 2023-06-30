#!/bin/bash

echo "Starting server in endless loop... (Press Ctrl+C or kill process with <PID: $$> to stop)"

cd ..

while [[ true ]]; do
    wine64 ./run.exe
done