#!/usr/bin/env python3
"""Debug pattern library collision issues."""

from lego_architect.core.data_structures import BuildState
from lego_architect.patterns import PatternLibrary
from lego_architect.validation import PhysicalValidator

# Test base pattern
build = BuildState()
base_parts = PatternLibrary.create_base(
    build_state=build,
    start_x=0,
    start_z=0,
    width=8,
    length=8,
    color=71,
)

print(f"Created {len(base_parts)} base parts")
print(f"Total parts in build: {len(build.parts)}")

# Show first few parts
for i, part in enumerate(build.parts[:5]):
    min_c, max_c = part.get_bounding_box()
    print(f"Part {i}: {part.part_id} at {part.position}, bbox: {min_c} → {max_c}")

# Validate
validator = PhysicalValidator()
result = validator.validate_build(build)

print(f"\nValidation result: {result.is_valid}")
print(f"Errors: {len(result.errors)}")
for error in result.errors[:5]:
    print(f"  - {error}")
