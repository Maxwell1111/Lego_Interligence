# AI-Powered LEGO Architect

Transform natural language prompts into complete, physically valid LEGO builds using Claude AI.

## Features

- 🤖 **Natural Language Input**: Describe what you want to build in plain English
- 🧱 **Direct Brick Placement**: Claude places individual bricks for maximum creative freedom
- ✅ **Strict Physical Validation**: No floating parts, proper stud connections, stable structures
- 🔄 **Intelligent Refinement**: Unlimited LLM-driven iterations with user confirmation
- 📖 **Step-by-Step Instructions**: Sub-assembly based building sequences
- 📦 **Multiple Output Formats**: LDraw files, BOM, ASCII preview, instruction guides

## Installation

### Prerequisites

- Python 3.11 or higher
- Anthropic API key ([get one here](https://console.anthropic.com/))
- Optional: LDraw library for rendering ([download here](https://ldraw.org/))

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd Lego_inteligence
```

2. Install dependencies:
```bash
pip install -e .
```

3. Create `.env` file:
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

4. (Optional) Install development dependencies:
```bash
pip install -e ".[dev]"
```

## Quick Start

Generate a LEGO build from a prompt:

```bash
lego-architect generate "A small red spaceship"
```

### Example Session

```bash
$ lego-architect generate "A medieval castle tower"

🤖 AI-Powered LEGO Architect v1.0
📝 Prompt: A medieval castle tower

🤖 Understanding your request...
   ✓ Complete

📋 I'm planning to create:
   - Type: Building
   - Size: ~20 studs
   - Colors: Gray, dark gray
   - Style: Medieval, detailed

Does this match your vision? (y/n): y

🔄 Designing build (this may take 2-3 minutes)...
   ✓ Complete

✅ Build complete!
   - 234 pieces
   - 2 refinement iterations
   - $0.08 cost

     ╔═══╗
     ║▓▓▓║
     ║▓▓▓║
     ║▓▓▓║
     ╚═══╝

📦 Bill of Materials: builds/tower_20260101_143022_bom.txt
🗺️  3D Model: builds/tower_20260101_143022.ldr
📖 Instructions: builds/tower_20260101_143022_instructions.md

Open in LDView? (y/n):
```

## Usage

### Basic Commands

```bash
# Generate a build
lego-architect generate "your prompt here"

# With options
lego-architect generate "a spaceship" --size medium --colors red blue --max-pieces 200

# List previous builds
lego-architect list-builds

# Show details of a build
lego-architect show <build-id>
```

### Command Options

- `--size`: Build size constraint (small/medium/large)
- `--colors`: Preferred colors
- `--max-pieces`: Maximum number of pieces
- `--output-dir`: Output directory (default: ./builds)
- `--no-ascii`: Skip ASCII preview
- `--auto-open`: Automatically open LDraw file

## Architecture

### Core Components

- **Data Structures** (`lego_architect/core`): Coordinate systems, part definitions, build state
- **Validation** (`lego_architect/validation`): Collision detection, connection validation, stability checking
- **Patterns** (`lego_architect/patterns`): Parametric templates for common structures (walls, bases, wings)
- **LLM Engine** (`lego_architect/llm`): Claude API integration with prompt caching
- **Orchestrator** (`lego_architect/orchestrator`): Coordinates generation and refinement
- **Output Generation** (`lego_architect/generation`): BOM, LDraw export, instructions, ASCII rendering
- **CLI** (`lego_architect/cli`): Command-line interface

### Coordinate System

The system uses a hybrid coordinate approach:

- **Stud Grid** (high-level): Integer coordinates in stud/plate units for LLM reasoning
- **LDraw Units** (low-level): Floating-point LDU for precise rendering and export

```
Conversions:
- 1 stud = 20 LDU (X/Z plane)
- 1 plate = 8 LDU (Y axis)
- 1 brick = 3 plates = 24 LDU
```

## Development

### Project Structure

```
lego_architect/
├── core/                 # Core data structures
│   └── data_structures.py
├── validation/           # Physical validation
│   └── validator.py
├── patterns/             # Pattern library
│   └── library.py
├── llm/                  # LLM integration
│   └── engine.py
├── orchestrator/         # Build orchestration
│   └── orchestrator.py
├── generation/           # Output generation
│   ├── bom.py
│   ├── ldraw.py
│   ├── instructions.py
│   └── ascii_renderer.py
├── cli/                  # CLI interface
│   └── cli.py
└── config.py            # Configuration
```

### Running Tests

```bash
pytest
```

### Code Quality

```bash
# Format code
black lego_architect/

# Lint
ruff lego_architect/

# Type check
mypy lego_architect/
```

## Technical Details

### LLM Strategy

- **Model**: Claude Sonnet 4 for initial generation, Haiku for refinements (cost optimization)
- **Prompt Caching**: ~90% cost reduction using cached part catalog (~5k tokens)
- **Tool Calling**: Direct `place_brick` calls with smart error suggestions
- **Refinement**: Unlimited iterations with user confirmation after each failed validation

### Validation

1. **Collision Detection**: AABB (Axis-Aligned Bounding Box) algorithm
2. **Connection Validation**: Stud/tube alignment checking, connection graph
3. **Stability Analysis**: Center of gravity, height-to-width ratio, support analysis

### Part Library

- **Initial Support**: 500+ parts (bricks, plates, slopes, tiles, Technic, connectors)
- **Hybrid Approach**: Top 100 parts manually curated, remaining 400 auto-extracted from LDraw
- **Categories**: Shallow taxonomy (5-10 top-level categories) for efficient LLM understanding

## Optimization

The system achieves <$0.10 cost per build through:

- **Prompt Caching**: Static part catalog cached (90% token savings)
- **Pattern Library**: Pre-validated templates for common structures
- **Smart Model Routing**: Expensive model for creative work, cheaper for refinements
- **Batch Processing**: Template expansion reduces individual brick placements

## Limitations

- Currently supports 500 parts (expandable to full LDraw library)
- Strict physical validation (no creative liberties with floating parts)
- CLI-only interface (web interface planned)
- Single-user mode (multi-user collaboration in future)

## Roadmap

- [ ] Web interface with 3D preview
- [ ] Expand to full LDraw part library (45,000+ parts)
- [ ] Multi-user collaborative building
- [ ] Build remixing and modification
- [ ] Custom part support
- [ ] Alternative LLM backends (GPT-4, local models)
- [ ] Mobile app
- [ ] Integration with Bricklink/BrickOwl for part purchasing

## Contributing

Contributions welcome! Please see [TECHNICAL_SPEC.md](TECHNICAL_SPEC.md) for detailed architecture documentation.

## License

MIT License - see LICENSE file for details

## Acknowledgments

- [LDraw](https://ldraw.org/) for the LEGO CAD standard
- [Anthropic](https://anthropic.com/) for Claude AI
- LEGO community for inspiration

---

**Note**: LEGO® is a trademark of the LEGO Group of companies which does not sponsor, authorize or endorse this project.
