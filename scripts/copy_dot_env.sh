#!/bin/bash

# Check and copy root .env file
if [ -f "../tac-4/.env" ]; then
    cp ../tac-4/.env .env
    echo "Successfully copied ../tac-4/.env to .env"
else
    echo "Warning: ../tac-4/.env does not exist"
fi

# Check and copy server .env file
if [ -f "../tac-4/app/server/.env" ]; then
    cp ../tac-4/app/server/.env app/server/.env
    echo "Successfully copied ../tac-4/app/server/.env to app/server/.env"
else
    echo "Error: ../tac-4/app/server/.env does not exist"
    exit 1
fi