#!/bin/bash

PORT=8080
cd src
gunicorn -b 127.0.0.1:${PORT} --worker-class eventlet -w 1 app:app
