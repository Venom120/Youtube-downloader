#!/bin/bash
set -e

echo ""
echo "=========================================="
echo "Starting YouTube Downloader Backend"
echo "=========================================="
echo ""

# Run cookie validation test
echo "Running cookie validation test..."
python /app/test_cookies.py

# Check exit code
COOKIE_TEST_EXIT=$?

if [ $COOKIE_TEST_EXIT -eq 0 ]; then
    echo ""
    echo "✅ Cookie validation passed!"
    echo "Starting application server..."
    echo ""
else
    echo ""
    echo "⚠️  Cookie validation failed!"
    echo ""
    
    # Check if cookies file exists
    if [ ! -f "/app/cookies/cookies.txt" ]; then
        echo "ℹ️  No cookies file found - starting in GUEST mode"
        echo "   Some videos may be restricted or unavailable"
        echo ""
    else
        echo "❌ Cookies file exists but validation failed!"
        echo "   Downloads will likely FAIL due to authentication issues"
        echo ""
        echo "🔧 RECOMMENDED ACTION:"
        echo "   1. Stop this container"
        echo "   2. Fix your cookies.txt file (see instructions above)"
        echo "   3. Restart the container"
        echo ""
        echo "⚠️  Proceeding anyway in 10 seconds..."
        echo "   Press Ctrl+C to stop and fix the issue"
        echo ""
        
        # Give user time to cancel
        for i in {10..1}; do
            echo -n "$i... "
            sleep 1
        done
        echo ""
        echo ""
        echo "⚠️  Starting server with INVALID cookies!"
        echo ""
    fi
fi

# Start the application
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload
