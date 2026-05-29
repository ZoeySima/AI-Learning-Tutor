#!/usr/bin/env bash
# AI Learning Tutor - Web launch script (macOS/Linux)

set -e

echo "Checking dependencies..."
python3 -m pip install -q -r requirements.txt -r requirements-web.txt

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo ""
    echo "ERROR: ANTHROPIC_API_KEY environment variable not set."
    echo ""
    echo "Please set it first:"
    echo "  export ANTHROPIC_API_KEY=sk-ant-..."
    echo ""
    exit 1
fi

echo "Starting AI Learning Tutor Web..."
echo ""
python3 -m web.server
