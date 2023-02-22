#!/bin/bash

cd /app
if [[ "${RUNNING_MODE}" == "http" ]]; then
    python http_service.py
else
    xpra start --no-daemon --html=on --start-child="xterm -e 'python bot.py 2>&1 | tee /tmp/log.txt'"  --exit-with-children
fi
