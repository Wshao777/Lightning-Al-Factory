#!/bin/bash
# Commercial-Al-Smart Setup Script

echo "Installing core dependencies for Lightning AI Factory..."

pip install -r "$(dirname "$0")/requirements.txt"

echo "Setup complete."
