# AI-Powered LEGO Architect - Usage Examples

## Quick Start

### 1. Setup

```bash
# Install dependencies
pip install -e .

# Create .env file with your API key
echo "ANTHROPIC_API_KEY=your_key_here" > .env
```

### 2. Simple Usage

```python
from lego_architect.core import BuildState
from lego_architect.llm import LLMEngine
from lego_architect.validation import PhysicalValidator

# Initialize engine
engine = LLMEngine()

# Create a build from natural language
build = BuildState(name="My Creation")
result = engine.generate_build("A small red tower", build)

print(f"Generated {len(build.parts)} parts")
print(f"Cost: ${result.tokens_used * 0.000003:.4f}")

# Validate
validator = PhysicalValidator()
validation = validator.validate_build(build)

if validation.is_valid:
    print("✅ Build is valid!")
else:
    print(f"❌ Errors: {validation.errors}")

    # Refine if needed
    result = engine.refine_build(build, validation.errors, iteration=1)
```

## Advanced Usage

### With Iteration Loop

```python
from lego_architect.core import BuildState
from lego_architect.llm import LLMEngine
from lego_architect.validation import PhysicalValidator

engine = LLMEngine()
validator = PhysicalValidator()
build = BuildState(name="Complex Build")

# Initial generation
result = engine.generate_build("A medieval castle tower", build)

# Refinement loop
max_iterations = 5
for iteration in range(1, max_iterations + 1):
    validation = validator.validate_build(build)

    if validation.is_valid:
        print(f"✅ Valid after {iteration} iteration(s)")
        break

    print(f"Iteration {iteration}: {len(validation.errors)} errors")
    result = engine.refine_build(build, validation.errors, iteration)
else:
    print("⚠️ Max iterations reached")

# Show results
print(f"\nFinal build:")
print(f"- Parts: {len(build.parts)}")
print(f"- Dimensions: {build.get_dimensions()}")
print(f"- Total tokens: {result.tokens_used}")
```

### Export to LDraw

```python
# After generating a valid build...

# Export to LDraw format
with open("my_build.ldr", "w") as f:
    f.write("0 AI-Generated LEGO Build\n")
    f.write(f"0 Name: {build.name}\n")
    f.write("0 Author: LEGO Architect AI\n\n")

    for part in build.parts:
        f.write(part.to_ldraw_line() + "\n")

print("Exported to my_build.ldr")
# Open in LDView, Bricklink Studio, or other LDraw viewer
```

### Generate BOM

```python
# Get bill of materials
bom = build.get_bom()

print("Bill of Materials:")
for (part_id, color), quantity in sorted(bom.items()):
    print(f"{quantity:3d}× Part {part_id} (Color {color})")

# Calculate total pieces
total = sum(bom.values())
print(f"\nTotal pieces: {total}")
```

## API Reference

### LLMEngine

```python
engine = LLMEngine()
```

**Methods:**

- `generate_build(prompt: str, build_state: BuildState) -> LLMResult`
  - Generate build from natural language prompt
  - Uses Claude Sonnet for maximum quality
  - Returns token usage and any errors

- `refine_build(build_state: BuildState, validation_errors: List[str], iteration: int) -> LLMResult`
  - Refine build based on validation errors
  - Uses Claude Haiku for cost efficiency (iterations > 1)
  - Returns token usage

### LLMResult

```python
@dataclass
class LLMResult:
    success: bool           # Whether generation succeeded
    tokens_used: int        # Total tokens consumed
    cached_tokens: int      # Tokens from cache (savings)
    response: Any          # Full Claude API response
    errors: List[str]      # Any tool execution errors
```

## Cost Optimization

### Prompt Caching

The system prompt (part catalog + rules) is cached automatically:

```python
# First call: Full cost (~4,200 tokens)
result1 = engine.generate_build("a tower", build1)
print(f"Cached: {result1.cached_tokens}")  # 0

# Second call: Cached (~90% savings)
result2 = engine.generate_build("a house", build2)
print(f"Cached: {result2.cached_tokens}")  # ~3,800
```

### Model Routing

```python
# Generation uses Sonnet (high quality)
result = engine.generate_build(prompt, build)

# Refinements use Haiku (5-10x cheaper)
for i in range(1, 5):
    result = engine.refine_build(build, errors, iteration=i)
    # Uses Haiku for i > 1
```

### Pattern Library

Use patterns to reduce token usage:

```python
# Instead of placing 50 individual bricks...
# Just describe using patterns
prompt = """
A house with:
- 16×16 base
- Four walls, 8 studs tall
- Corner columns for support
"""

# Claude will use create_base(), create_wall(), create_column()
# Single tool call creates entire structure
```

## Examples

### Example 1: Simple Tower

```python
from lego_architect.core import BuildState
from lego_architect.llm import LLMEngine

engine = LLMEngine()
build = BuildState()

result = engine.generate_build("A 6-brick tall red tower", build)

print(f"Parts: {len(build.parts)}")
# Output: Parts: 6

for part in build.parts:
    print(f"- {part.part_name} at {part.position}")
# Output:
# - Brick 2×4 at (0, 0, 0)
# - Brick 2×4 at (0, 0, 3)
# - Brick 2×4 at (0, 0, 6)
# ...
```

### Example 2: Spaceship

```python
build = BuildState()
result = engine.generate_build(
    "A small sleek spaceship with wings and a cockpit",
    build
)

# Claude will:
# 1. Create base fuselage
# 2. Add wings using slopes
# 3. Create cockpit area
# 4. Ensure everything connects properly
```

### Example 3: With Validation

```python
from lego_architect.validation import PhysicalValidator

engine = LLMEngine()
validator = PhysicalValidator()
build = BuildState()

# Generate
result = engine.generate_build("A bridge with supports", build)

# Validate
validation = validator.validate_build(build)

if not validation.is_valid:
    print("Validation failed:")
    for error in validation.errors:
        print(f"  - {error}")

    # Show suggestions
    for suggestion in validation.suggestions:
        print(f"  💡 {suggestion}")
```

## Error Handling

```python
try:
    result = engine.generate_build(prompt, build)

    if not result.success:
        print("Generation had errors:")
        for error in result.errors:
            print(f"  - {error}")

except Exception as e:
    print(f"API error: {e}")
    # Check API key, network, etc.
```

## Testing Without API Key

You can test the structure without an API key:

```python
# Test tool handlers directly
from lego_architect.core import BuildState
from lego_architect.llm import LLMEngine

engine = LLMEngine()
build = BuildState()

# Test place_brick handler
args = {
    "part_id": "3001",
    "color": 4,
    "stud_x": 0,
    "stud_z": 0,
    "plate_y": 0,
}

error = engine._handle_place_brick(args, build)

if error:
    print(f"Error: {error}")
else:
    print(f"Success! Added {build.parts[0].part_name}")
```

## Tips

1. **Be specific in prompts**: "A 10-stud wide red spaceship" vs "a spaceship"
2. **Use colors**: Claude understands color codes (1=blue, 4=red, etc.)
3. **Mention size**: Small/medium/large or exact dimensions
4. **Iterate**: If first attempt isn't perfect, refine with validation errors
5. **Use patterns**: Mention "walls" or "base" to trigger efficient patterns

## Troubleshooting

### "ANTHROPIC_API_KEY not found"
```bash
# Create .env file
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
```

### "Unknown part ID"
```python
# Check available parts
from lego_architect.llm import LLMEngine
engine = LLMEngine()
print(engine.part_catalog.keys())
```

### "Collision detected"
```python
# LLM will get suggestions automatically
# You can also manually check:
from lego_architect.validation import PhysicalValidator
validator = PhysicalValidator()
result = validator.quick_validate_placement(build, new_part)
print(result['suggestions'])
```

## Performance

- **Simple build** (10 parts): ~5-10 seconds, ~2,000 tokens
- **Medium build** (50 parts): ~15-30 seconds, ~5,000 tokens
- **Complex build** (200 parts): ~1-2 minutes, ~15,000 tokens

With caching:
- **Second build**: 90% faster token processing
- **Cost**: 90% lower for cached portions

## Next Steps

See full documentation:
- `README.md` - Installation and overview
- `TECHNICAL_SPEC.md` - Detailed architecture
- `demo_llm.py` - Interactive demonstrations
