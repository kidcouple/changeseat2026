#!/bin/bash
# Kill any process on port 8080
echo "Killing process on port 8080..."
lsof -ti:8080 | xargs kill -9 2>/dev/null

# Start the server
echo "Starting server..."
python3 app.py
