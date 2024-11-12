#!/bin/bash

# En dark-block-watch/run-dev.sh
echo "Starting DarkBlock Watch development environment..."

# Iniciar backend
cd backend
source venv/bin/activate
echo "Starting backend server..."
uvicorn main:app --reload &

# Esperar unos segundos para que el backend inicie
sleep 3

# Iniciar frontend
cd ../frontend
echo "Starting frontend server..."
npm start

# Mantener el script corriendo
wait
