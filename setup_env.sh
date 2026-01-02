#!/bin/bash
# Setup script for AI-Powered LEGO Architect

echo "🔧 Setting up AI-Powered LEGO Architect"
echo ""

# Check if .env already exists
if [ -f ".env" ]; then
    echo "✅ .env file already exists"
    echo ""

    # Check if API key is set
    if grep -q "ANTHROPIC_API_KEY=sk-" .env 2>/dev/null; then
        echo "✅ API key appears to be configured"
    else
        echo "⚠️  API key may not be configured"
        echo "   Edit .env and add your Anthropic API key:"
        echo "   ANTHROPIC_API_KEY=sk-ant-your-key-here"
    fi
else
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ Created .env file"
    echo ""
    echo "⚠️  Please edit .env and add your Anthropic API key:"
    echo "   ANTHROPIC_API_KEY=sk-ant-your-key-here"
    echo ""
    echo "   Get your API key from: https://console.anthropic.com/"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Current Configuration:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f ".env" ]; then
    # Show non-sensitive config
    grep -v "API_KEY" .env 2>/dev/null || echo "No additional config"

    # Check API key (show masked)
    if grep -q "ANTHROPIC_API_KEY=" .env; then
        api_key=$(grep "ANTHROPIC_API_KEY=" .env | cut -d= -f2)
        if [ -n "$api_key" ] && [ "$api_key" != "your_anthropic_api_key_here" ]; then
            echo "ANTHROPIC_API_KEY=sk-ant-****...${api_key: -4}"
        else
            echo "ANTHROPIC_API_KEY=<NOT SET>"
        fi
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Next Steps:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Run tests:"
echo "   ./test.sh"
echo ""
echo "2. Try the demos:"
echo "   python3 demo.py              # Manual building (no API key needed)"
echo "   python3 demo_llm.py          # AI-powered demo (requires API key)"
echo "   python3 demo_orchestrator.py # Full orchestration (requires API key)"
echo ""
echo "3. Or use Make commands:"
echo "   make test"
echo "   make demo"
echo "   make demo-llm"
echo ""
