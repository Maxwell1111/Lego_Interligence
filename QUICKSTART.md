# Quick Start Guide - AI-Powered LEGO Architect

Get up and running in 3 steps!

---

## ✅ Step 1: Run Tests (No API Key Needed)

Verify everything works:

```bash
./test.sh
```

This runs 56 tests:
- ✅ 6 core functionality tests
- ✅ 6 LLM engine structure tests
- ✅ 7 orchestrator tests
- ✅ 37 unit tests

**All tests should pass!**

---

## ✅ Step 2: Try Manual Building (No API Key Needed)

Run the demo to see manual LEGO building:

```bash
python3 demo.py
```

This demonstrates:
- Creating builds programmatically
- Physical validation (collision, connections, stability)
- Pattern library usage
- Coordinate system
- LDraw export

---

## 🤖 Step 3: Set Up AI-Powered Generation (Requires API Key)

### 3a. Get Your API Key

1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Get your API key (starts with `sk-ant-`)

### 3b. Configure Environment

```bash
# Run setup helper
./setup_env.sh

# Or manually:
cp .env.example .env
# Edit .env and add your key:
# ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### 3c. Try AI-Powered Demos

```bash
# AI-powered generation
python3 demo_llm.py

# Full orchestration with refinement
python3 demo_orchestrator.py

# Or use Make:
make demo-llm
make demo-orchestrator
```

---

## 🎮 Quick Commands

```bash
# Setup
./install.sh           # Create venv and install deps

# Tests
./test.sh              # Run all tests
make test              # Same as above

# Demos
python3 demo.py                    # Manual building
python3 demo_llm.py                # AI-powered
python3 demo_orchestrator.py       # Full workflow

# Make shortcuts
make demo              # Run manual demo
make demo-llm          # Run AI demo
make demo-orchestrator # Run orchestrator demo

# Docker
make docker-build      # Build Docker image
make docker-run        # Run in container

# Development
make lint              # Run linters
make format            # Format code with black
make clean             # Remove build artifacts
```

---

## 📊 What's Implemented (67% Complete)

### ✅ Complete Modules
1. **Core Data Structures** - Hybrid coordinate system, part management
2. **Physical Validation** - Collision, connections, stability
3. **Pattern Library** - Pre-validated structure templates
4. **LLM Engine** - Claude API integration with prompt caching
5. **Build Orchestrator** - Full workflow coordination
6. **Configuration** - Environment management

### 🚧 Remaining Modules
7. **Output Generation** - BOM, instructions, ASCII rendering
8. **CLI Interface** - Click-based command interface

---

## 💡 Example: AI-Powered Generation

```python
from lego_architect.orchestrator import BuildOrchestrator

# Create orchestrator
orchestrator = BuildOrchestrator()

# Generate from natural language
result = orchestrator.generate_build(
    prompt="A small red spaceship with wings",
    auto_clarify=True,
    max_refinement_iterations=5
)

# Check results
if result.success:
    print(f"✅ Generated {len(result.build_state.parts)} parts")
    print(f"💰 Cost: ${result.metrics.total_cost_usd:.4f}")
    print(f"⏱️  Time: {result.metrics.duration_seconds:.1f}s")

    # Get BOM
    bom = result.build_state.get_bom()
    print(f"📋 {len(bom)} unique parts needed")

    # Export to LDraw
    with open("spaceship.ldr", "w") as f:
        for part in result.build_state.parts:
            f.write(part.to_ldraw_line() + "\n")
```

---

## 📈 Cost Optimization

The system achieves **<$0.10 per build** through:

- ✅ **Prompt Caching**: 90% token reduction (4,200 char system prompt cached)
- ✅ **Model Routing**: Sonnet for generation ($3/M), Haiku for refinement ($1/M)
- ✅ **Pattern Library**: Pre-validated templates reduce individual placements
- ✅ **Smart Assistance**: Error suggestions help LLM self-correct

**Typical costs:**
- Simple build (10-30 parts): $0.02-0.03
- Medium build (50-100 parts): $0.04-0.06
- Complex build (150+ parts): $0.08-0.12

---

## 🆘 Troubleshooting

### API Key Not Found
```bash
# Check .env exists
ls -la .env

# Verify key is set
grep ANTHROPIC_API_KEY .env

# Re-run setup
./setup_env.sh
```

### Tests Failing
```bash
# Ensure dependencies installed
pip install -e .

# Run individual test suites
python3 quick_test.py
python3 test_llm_engine.py
python3 test_orchestrator.py
```

### EOFError in Demos
The demos now handle both interactive and non-interactive environments automatically. This should not occur, but if it does:
```bash
# Force non-interactive mode
python3 demo.py < /dev/null
```

---

## 📚 Documentation

- **README.md** - Full project overview
- **TECHNICAL_SPEC.md** - Detailed architecture (1,900+ lines)
- **STATUS.md** - Current implementation status
- **USAGE_EXAMPLE.md** - API examples
- **LLM_ENGINE_SUMMARY.md** - LLM engine details
- **ORCHESTRATOR_SUMMARY.md** - Orchestrator details

---

## 🚀 Next Steps

1. ✅ Run tests: `./test.sh`
2. ✅ Try manual demo: `python3 demo.py`
3. 🤖 Set up API key: `./setup_env.sh`
4. 🤖 Try AI demos: `python3 demo_llm.py`
5. 🔨 Contribute: See remaining modules (output generation, CLI)

---

**Ready to build with AI! 🧱🤖**

Repository: https://github.com/Maxwell1111/Lego_Interligence
