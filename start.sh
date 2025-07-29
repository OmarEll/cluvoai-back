#!/bin/bash

echo "🚀 Starting Cluvo.ai API..."
echo "📦 Python version: $(python --version)"
echo "🔧 Working directory: $(pwd)"
echo "📁 Files in current directory:"
ls -la

echo "🔍 Checking environment variables..."
echo "PORT: $PORT"
echo "RAILWAY_ENVIRONMENT: $RAILWAY_ENVIRONMENT"
echo "OPENAI_API_KEY: ${OPENAI_API_KEY:0:10}..."
echo "MONGO_HOST: $MONGO_HOST"

echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "🚀 Starting application..."
python main.py 