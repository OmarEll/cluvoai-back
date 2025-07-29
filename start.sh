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

echo "🔍 Checking Python path and imports..."
python -c "import sys; print('Python path:', sys.path)"
python -c "import fastapi; print('FastAPI version:', fastapi.__version__)"
python -c "import uvicorn; print('Uvicorn version:', uvicorn.__version__)"

echo "🧪 Testing import of main application..."
python -c "
try:
    from main import app
    print('✅ Main application imported successfully')
except Exception as e:
    print(f'❌ Error importing main application: {e}')
    import traceback
    traceback.print_exc()
"

echo "🚀 Starting application..."
echo "🔗 Will bind to 0.0.0.0:${PORT:-8000}"

# Start the application with explicit error handling
python main.py 2>&1 | tee /tmp/app.log
echo "📋 Application exit code: $?"

# If application exits, show the last few lines of the log
echo "📄 Last 20 lines of application log:"
tail -20 /tmp/app.log 