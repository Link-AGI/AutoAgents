#!/bin/sh

cd /app/autoagents
python main.py --mode service &
sleep 2
