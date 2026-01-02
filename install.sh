#!/bin/bash
# Install script for LEGO Architect

set -e

echo "🔧 Installing AI-Powered LEGO Architect..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install package in editable mode
echo "📥 Installing dependencies..."
pip install -e .

# Install development dependencies
echo "📥 Installing development dependencies..."
pip install pytest black ruff mypy

echo ""
echo "✅ Installation complete!"
echo ""
echo "To activate the environment:"
echo "  source venv/bin/activate"
echo ""
echo "To run tests:"
echo "  python quick_test.py"
echo ""
echo "To run demo:"
echo "  python demo.py"
echo ""
