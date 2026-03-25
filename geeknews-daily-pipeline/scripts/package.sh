#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="/tmp/lambda-build-$$"
ZIP_NAME="geeknews-daily-pipeline.zip"

cd "$PROJECT_ROOT"

# Cleanup
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Install dependencies
pip install -r requirements.txt -t "$BUILD_DIR" --quiet

# Copy source code
cp -r src/* "$BUILD_DIR/"

# Create ZIP excluding forbidden files
cd "$BUILD_DIR"
zip -r "$PROJECT_ROOT/$ZIP_NAME" . -x "*.pyc" "__pycache__/*" "test_*" ".env" "*.pyc"

# Cleanup
cd "$PROJECT_ROOT"
rm -rf "$BUILD_DIR"

# Output
echo "Created: $ZIP_NAME"
echo "Size: $(stat -f%z "$ZIP_NAME" 2>/dev/null || stat -c%s "$ZIP_NAME") bytes"