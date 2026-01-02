#!/usr/bin/env python3
"""
Test LLM Engine structure and tool handling.

Note: Actual API calls require ANTHROPIC_API_KEY in .env
This test verifies the engine structure without making API calls.
"""

from lego_architect.core.data_structures import BuildState
from lego_architect.llm import LLMEngine


def test_engine_initialization():
    """Test LLM engine can be initialized."""
    print("Testing LLM engine initialization...")

    try:
        engine = LLMEngine()
        print(f"✅ Engine initialized")
        print(f"   - Part catalog: {len(engine.part_catalog)} parts")
        print(f"   - System prompt: {len(engine.system_prompt_cached)} characters")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_part_catalog():
    """Test part catalog structure."""
    print("\nTesting part catalog...")

    engine = LLMEngine()

    # Check catalog structure
    assert len(engine.part_catalog) > 0, "Catalog should have parts"

    # Check a specific part
    brick_2x4 = engine.part_catalog.get("3001")
    assert brick_2x4 is not None, "Should have 2×4 brick"
    assert brick_2x4["name"] == "Brick 2×4"
    assert brick_2x4["dimensions"]["studs_width"] == 2
    assert brick_2x4["dimensions"]["studs_length"] == 4
    assert brick_2x4["dimensions"]["plates_height"] == 3

    print(f"✅ Part catalog valid ({len(engine.part_catalog)} parts)")

    # Show parts by category
    categories = {}
    for part_id, part in engine.part_catalog.items():
        cat = part["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(part_id)

    for cat, parts in categories.items():
        print(f"   - {cat}: {len(parts)} parts")

    return True


def test_tool_definitions():
    """Test tool definitions structure."""
    print("\nTesting tool definitions...")

    engine = LLMEngine()
    tools = engine._get_tool_definitions()

    assert len(tools) == 4, "Should have 4 tools"

    tool_names = [tool["name"] for tool in tools]
    expected = ["place_brick", "create_base", "create_wall", "create_column"]

    for expected_name in expected:
        assert expected_name in tool_names, f"Should have {expected_name} tool"

    print(f"✅ Tool definitions valid")
    for tool in tools:
        print(f"   - {tool['name']}: {tool['description'][:50]}...")

    return True


def test_tool_handlers():
    """Test tool handlers work correctly."""
    print("\nTesting tool handlers...")

    engine = LLMEngine()
    build = BuildState()

    # Test place_brick handler
    args = {
        "part_id": "3001",
        "color": 4,
        "stud_x": 0,
        "stud_z": 0,
        "plate_y": 0,
        "rotation": 0,
    }

    error = engine._handle_place_brick(args, build)

    if error:
        print(f"❌ place_brick failed: {error}")
        return False

    assert len(build.parts) == 1, "Should have 1 part"
    print(f"✅ place_brick handler works (added {build.parts[0].part_name})")

    # Test create_base handler
    build2 = BuildState()
    args = {"start_x": 0, "start_z": 0, "width": 8, "length": 8, "color": 71}

    error = engine._handle_create_base(args, build2)

    if error:
        print(f"❌ create_base failed: {error}")
        return False

    assert len(build2.parts) > 0, "Should have parts"
    print(f"✅ create_base handler works (added {len(build2.parts)} parts)")

    # Test create_wall handler
    build3 = BuildState()
    args = {
        "start_x": 0,
        "start_z": 0,
        "start_y": 0,
        "length": 8,
        "height": 9,
        "direction": "x",
        "color": 4,
    }

    error = engine._handle_create_wall(args, build3)

    if error:
        print(f"❌ create_wall failed: {error}")
        return False

    assert len(build3.parts) > 0, "Should have parts"
    print(f"✅ create_wall handler works (added {len(build3.parts)} parts)")

    return True


def test_collision_feedback():
    """Test that collision detection provides feedback."""
    print("\nTesting collision feedback...")

    engine = LLMEngine()
    build = BuildState()

    # Add a brick
    args1 = {
        "part_id": "3001",
        "color": 4,
        "stud_x": 0,
        "stud_z": 0,
        "plate_y": 0,
        "rotation": 0,
    }
    engine._handle_place_brick(args1, build)

    # Try to place overlapping brick
    args2 = {
        "part_id": "3001",
        "color": 1,
        "stud_x": 1,
        "stud_z": 1,
        "plate_y": 0,
        "rotation": 0,
    }

    error = engine._handle_place_brick(args2, build)

    assert error is not None, "Should detect collision"
    assert "collision" in error.lower(), "Error should mention collision"

    print(f"✅ Collision detection works")
    print(f"   Error message: {error[:80]}...")

    # Check for suggestions
    assert "suggestion" in error.lower() or "try" in error.lower(), "Should have suggestions"
    print(f"   ✓ Includes suggestions for LLM")

    return True


def test_prompt_caching_structure():
    """Test prompt caching structure."""
    print("\nTesting prompt caching structure...")

    engine = LLMEngine()

    # Check system prompt is substantial (for caching)
    prompt_len = len(engine.system_prompt_cached)
    assert prompt_len > 1000, "System prompt should be substantial for caching"

    print(f"✅ Prompt caching structure valid")
    print(f"   - System prompt: {prompt_len} characters")
    print(f"   - Contains part catalog: {'PART CATALOG' in engine.system_prompt_cached}")
    print(f"   - Contains building rules: {'BUILDING RULES' in engine.system_prompt_cached}")

    return True


def main():
    """Run all tests."""
    print("=" * 70)
    print("  LLM ENGINE STRUCTURE TEST")
    print("=" * 70)

    tests = [
        test_engine_initialization,
        test_part_catalog,
        test_tool_definitions,
        test_tool_handlers,
        test_collision_feedback,
        test_prompt_caching_structure,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except AssertionError as e:
            print(f"❌ Assertion failed: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ Error: {e}")
            failed += 1

    print("\n" + "=" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70)

    if failed == 0:
        print("\n🎉 LLM Engine structure is valid!")
        print("\n📝 Next steps:")
        print("   1. Add ANTHROPIC_API_KEY to .env file")
        print("   2. Run: python3 demo_llm.py (to test with real API)")
        print("   3. Use the engine in the orchestrator")
        print()
    else:
        print(f"\n⚠️  {failed} test(s) failed.")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit(main())
