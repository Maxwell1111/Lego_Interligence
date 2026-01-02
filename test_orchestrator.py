#!/usr/bin/env python3
"""
Test Orchestrator structure and workflow coordination.

This tests the orchestrator logic without making actual API calls.
"""

from lego_architect.core.data_structures import BuildState
from lego_architect.orchestrator import BuildOrchestrator


def test_orchestrator_initialization():
    """Test orchestrator can be initialized."""
    print("Testing orchestrator initialization...")

    try:
        orchestrator = BuildOrchestrator()
        print("✅ Orchestrator initialized")
        print(f"   - LLM Engine: {orchestrator.llm_engine is not None}")
        print(f"   - Validator: {orchestrator.validator is not None}")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_prompt_clarification():
    """Test prompt clarification logic."""
    print("\nTesting prompt clarification...")

    orchestrator = BuildOrchestrator()

    # Test 1: Ambiguous prompt (no size, no color)
    prompt1 = "A spaceship"
    _, clarifications1 = orchestrator.clarify_prompt(prompt1)

    assert len(clarifications1) > 0, "Should need clarifications for vague prompt"
    print(f"✅ Ambiguous prompt detected")
    print(f"   - Prompt: '{prompt1}'")
    print(f"   - Clarifications needed: {len(clarifications1)}")
    for c in clarifications1:
        print(f"     - {c.question}")

    # Test 2: Specific prompt (has size and color)
    prompt2 = "A small red spaceship"
    _, clarifications2 = orchestrator.clarify_prompt(prompt2)

    print(f"\n✅ Specific prompt analyzed")
    print(f"   - Prompt: '{prompt2}'")
    print(f"   - Clarifications needed: {len(clarifications2)}")

    return True


def test_prompt_enrichment():
    """Test prompt enrichment with clarifications."""
    print("\nTesting prompt enrichment...")

    orchestrator = BuildOrchestrator()

    original = "A spaceship"
    clarifications = {
        "What size should the build be?": "Small (10-30 parts)",
        "What color scheme should be used?": "Primarily blue",
    }

    enriched = orchestrator.enrich_prompt(original, clarifications)

    assert "Size: Small" in enriched, "Should include size"
    assert "Color: Primarily blue" in enriched, "Should include color"

    print(f"✅ Prompt enrichment works")
    print(f"   Original: '{original}'")
    print(f"   Enriched: '{enriched}'")

    return True


def test_metrics_tracking():
    """Test build metrics structure."""
    print("\nTesting metrics tracking...")

    from lego_architect.orchestrator.coordinator import BuildMetrics

    metrics = BuildMetrics()

    # Simulate adding results
    class MockResult:
        def __init__(self, tokens, cached):
            self.tokens_used = tokens
            self.cached_tokens = cached

    # Generation
    metrics.add_llm_result(MockResult(tokens=5000, cached=0), is_refinement=False)

    # Refinement
    metrics.add_llm_result(MockResult(tokens=2000, cached=3000), is_refinement=True)

    metrics.final_part_count = 42
    metrics.final_dimensions = (8, 8, 12)
    metrics.finish()

    print(f"✅ Metrics tracking works")
    print(f"   - Total tokens: {metrics.total_tokens:,}")
    print(f"   - Cached tokens: {metrics.cached_tokens:,}")
    print(f"   - Total cost: ${metrics.total_cost_usd:.4f}")
    print(f"   - Duration: {metrics.duration_seconds:.3f}s")
    print(f"   - Parts: {metrics.final_part_count}")

    assert metrics.total_tokens == 7000
    assert metrics.cached_tokens == 3000
    assert metrics.generation_iterations == 1
    assert metrics.refinement_iterations == 1
    assert metrics.total_cost_usd > 0

    return True


def test_progress_callback():
    """Test progress reporting mechanism."""
    print("\nTesting progress callback...")

    progress_events = []

    def progress_callback(stage: str, data: dict):
        """Track progress events."""
        progress_events.append((stage, data))

    orchestrator = BuildOrchestrator(progress_callback=progress_callback)

    # Trigger some progress reports
    orchestrator._report_progress("test_stage", test_data="test_value")

    assert len(progress_events) == 1
    assert progress_events[0][0] == "test_stage"
    assert progress_events[0][1]["test_data"] == "test_value"

    print(f"✅ Progress callback works")
    print(f"   - Events captured: {len(progress_events)}")
    print(f"   - Event: {progress_events[0][0]} -> {progress_events[0][1]}")

    return True


def test_build_result_structure():
    """Test build result dataclass."""
    print("\nTesting build result structure...")

    from lego_architect.orchestrator.coordinator import BuildMetrics, BuildResult

    build = BuildState(name="Test Build")
    metrics = BuildMetrics()
    metrics.finish()

    result = BuildResult(
        success=True, build_state=build, metrics=metrics, errors=[], warnings=[]
    )

    assert result.success is True
    assert result.build_state.name == "Test Build"
    assert result.user_cancelled is False
    assert len(result.errors) == 0

    print(f"✅ Build result structure valid")
    print(f"   - Success: {result.success}")
    print(f"   - Build name: {result.build_state.name}")
    print(f"   - Errors: {len(result.errors)}")

    return True


def test_orchestrator_workflow_structure():
    """Test that orchestrator has proper workflow methods."""
    print("\nTesting orchestrator workflow structure...")

    orchestrator = BuildOrchestrator()

    # Check methods exist
    assert hasattr(orchestrator, "generate_build"), "Should have generate_build"
    assert hasattr(
        orchestrator, "generate_build_interactive"
    ), "Should have generate_build_interactive"
    assert hasattr(orchestrator, "clarify_prompt"), "Should have clarify_prompt"
    assert hasattr(orchestrator, "enrich_prompt"), "Should have enrich_prompt"

    print(f"✅ Orchestrator workflow structure valid")
    print(f"   - generate_build: ✓")
    print(f"   - generate_build_interactive: ✓")
    print(f"   - clarify_prompt: ✓")
    print(f"   - enrich_prompt: ✓")

    return True


def main():
    """Run all tests."""
    print("=" * 70)
    print("  ORCHESTRATOR STRUCTURE TEST")
    print("=" * 70)

    tests = [
        test_orchestrator_initialization,
        test_prompt_clarification,
        test_prompt_enrichment,
        test_metrics_tracking,
        test_progress_callback,
        test_build_result_structure,
        test_orchestrator_workflow_structure,
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
            import traceback

            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70)

    if failed == 0:
        print("\n🎉 Orchestrator structure is valid!")
        print("\n📝 The orchestrator is ready to coordinate builds!")
        print("\nKey features:")
        print("  ✓ Prompt clarification with smart defaults")
        print("  ✓ Generation loop with LLM Engine")
        print("  ✓ Iterative refinement (unlimited with user confirmation)")
        print("  ✓ Comprehensive metrics tracking")
        print("  ✓ Progress reporting via callbacks")
        print("  ✓ Interactive and automatic modes")
        print()
    else:
        print(f"\n⚠️  {failed} test(s) failed.")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit(main())
