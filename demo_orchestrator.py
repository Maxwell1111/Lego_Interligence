#!/usr/bin/env python3
"""
Demo of the Build Orchestrator coordinating the full AI-powered workflow.

This demonstrates:
1. Prompt clarification with smart defaults
2. LLM-powered build generation
3. Physical validation
4. Iterative refinement
5. Comprehensive metrics tracking
6. Progress reporting

Requires: ANTHROPIC_API_KEY in .env file
"""

import sys

from lego_architect.config import config
from lego_architect.orchestrator import BuildOrchestrator


def safe_input(prompt="Press Enter to continue..."):
    """Safely handle input in both interactive and non-interactive environments."""
    if not sys.stdin.isatty():
        # Non-interactive environment, skip input
        print(f"[Auto-continuing in non-interactive mode]")
        return ""
    try:
        return input(prompt)
    except EOFError:
        print(f"\n[Auto-continuing]")
        return ""


def check_api_key():
    """Check if API key is configured."""
    if not config.ANTHROPIC_API_KEY:
        print("❌ ANTHROPIC_API_KEY not found!")
        print("\n📝 To use AI-powered generation:")
        print("   1. Create a .env file in the project root")
        print("   2. Add: ANTHROPIC_API_KEY=your_key_here")
        print("   3. Get your key from: https://console.anthropic.com/")
        return False
    return True


def demo_simple_generation():
    """Demo: Simple build generation with orchestrator."""
    print("=" * 70)
    print("DEMO 1: Simple Build Generation")
    print("=" * 70)

    prompt = "A small tower"

    print(f"\n📝 Prompt: '{prompt}'")
    print("\n🤖 Starting orchestrated build generation...")

    # Track progress
    progress_log = []

    def progress_callback(stage: str, data: dict):
        """Log progress events."""
        progress_log.append((stage, data))
        if stage == "start":
            print(f"\n▶ Starting generation: {data.get('prompt')}")
        elif stage == "generation_start":
            print(f"\n🎨 LLM Generation (iteration {data.get('iteration')})")
        elif stage == "generation_complete":
            print(
                f"   ✓ Generated {data.get('parts_count')} parts ({data.get('tokens'):,} tokens)"
            )
        elif stage == "validation_start":
            print(f"\n🔍 Validating build...")
        elif stage == "validation_complete":
            if data.get("is_valid"):
                print(f"   ✓ Build is valid!")
            else:
                print(f"   ⚠ Found {data.get('error_count')} validation errors")
        elif stage == "refinement_needed":
            print(f"\n🔧 Refinement needed (iteration {data.get('iteration')})")
            print(f"   Errors to fix: {data.get('error_count')}")
            for i, error in enumerate(data.get("errors", [])[:3], 1):
                print(f"      {i}. {error}")
        elif stage == "refinement_start":
            print(f"\n🎨 LLM Refinement (iteration {data.get('iteration')})")
        elif stage == "refinement_complete":
            print(
                f"   ✓ Refinement complete ({data.get('tokens'):,} tokens)"
            )
        elif stage == "success":
            print(f"\n✅ Build complete!")
        elif stage == "max_iterations_reached":
            print(
                f"\n⚠ Max iterations ({data.get('max_iterations')}) reached"
            )
            print(f"   Remaining errors: {data.get('remaining_errors')}")

    orchestrator = BuildOrchestrator(progress_callback=progress_callback)

    try:
        result = orchestrator.generate_build(
            prompt=prompt,
            build_name="AI Tower",
            auto_clarify=True,  # Use smart defaults
            max_refinement_iterations=3,
            auto_confirm_refinement=True,  # Auto-continue refinement
        )

        print("\n" + "=" * 70)
        print("RESULTS")
        print("=" * 70)

        print(f"\n✅ Success: {result.success}")
        print(f"   User cancelled: {result.user_cancelled}")

        if result.errors:
            print(f"\n❌ Errors ({len(result.errors)}):")
            for error in result.errors[:5]:
                print(f"   - {error}")

        if result.warnings:
            print(f"\n⚠️  Warnings ({len(result.warnings)}):")
            for warning in result.warnings:
                print(f"   - {warning}")

        print(f"\n📊 {result.metrics}")

        print(f"\n📦 Build state:")
        print(f"   - Name: {result.build_state.name}")
        print(f"   - Parts: {len(result.build_state.parts)}")

        if result.build_state.parts:
            print(f"\n🧱 First parts:")
            for i, part in enumerate(result.build_state.parts[:5]):
                print(f"   {i+1}. {part.part_name} at {part.position}")

            # BOM
            print(f"\n📋 Bill of Materials:")
            bom = result.build_state.get_bom()
            for (part_id, color), qty in list(bom.items())[:5]:
                print(f"   - {qty}× Part {part_id} (Color {color})")

        print(f"\n📈 Progress events: {len(progress_log)}")

        return result.success

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


def demo_with_clarifications():
    """Demo: Build with explicit clarifications."""
    print("\n" + "=" * 70)
    print("DEMO 2: Build with Clarifications")
    print("=" * 70)

    prompt = "A spaceship"

    print(f"\n📝 Original prompt: '{prompt}'")

    orchestrator = BuildOrchestrator()

    # Get clarifications
    _, clarifications = orchestrator.clarify_prompt(prompt)

    print(f"\n💡 Clarifications needed: {len(clarifications)}")
    for c in clarifications:
        print(f"\n   Q: {c.question}")
        print(f"      Suggestions: {', '.join(c.suggestions)}")
        print(f"      Default: {c.default}")

    # Provide answers
    answers = {
        "What size should the build be?": "Small (10-30 parts)",
        "What color scheme should be used?": "Primarily blue",
        "What style should it be?": "Simple/minimalist",
    }

    print(f"\n✏️  Provided answers:")
    for q, a in answers.items():
        print(f"   - {q}")
        print(f"     → {a}")

    enriched = orchestrator.enrich_prompt(prompt, answers)

    print(f"\n📝 Enriched prompt:")
    print(f"   {enriched}")

    print("\n🤖 Generating build with enriched prompt...")

    try:
        result = orchestrator.generate_build(
            prompt=prompt,
            build_name="Blue Spaceship",
            clarifications=answers,
            max_refinement_iterations=3,
            auto_confirm_refinement=True,
        )

        print(f"\n✅ Success: {result.success}")
        print(f"\n📊 Cost: ${result.metrics.total_cost_usd:.4f}")
        print(f"   Parts: {result.metrics.final_part_count}")

        return result.success

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def demo_metrics_comparison():
    """Demo: Show metrics for different build complexities."""
    print("\n" + "=" * 70)
    print("DEMO 3: Metrics Comparison")
    print("=" * 70)

    prompts = [
        ("Simple", "A 6-brick tall tower"),
        ("Medium", "A small house with walls"),
        ("Complex", "A spaceship with wings"),
    ]

    orchestrator = BuildOrchestrator()

    results = []

    for complexity, prompt in prompts:
        print(f"\n{'=' * 70}")
        print(f"{complexity}: '{prompt}'")
        print('=' * 70)

        try:
            result = orchestrator.generate_build(
                prompt=prompt,
                auto_clarify=True,
                max_refinement_iterations=2,
                auto_confirm_refinement=True,
            )

            results.append((complexity, result))

            print(f"\n✅ {complexity} build complete")
            print(f"   Parts: {result.metrics.final_part_count}")
            print(f"   Tokens: {result.metrics.total_tokens:,}")
            print(f"   Cost: ${result.metrics.total_cost_usd:.4f}")
            print(f"   Time: {result.metrics.duration_seconds:.1f}s")
            print(f"   Iterations: {result.metrics.total_iterations}")

        except Exception as e:
            print(f"\n❌ {complexity} build failed: {e}")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    print(f"\n{'Complexity':<12} {'Parts':<8} {'Tokens':<10} {'Cost':<10} {'Time':<8}")
    print("-" * 60)

    for complexity, result in results:
        print(
            f"{complexity:<12} "
            f"{result.metrics.final_part_count:<8} "
            f"{result.metrics.total_tokens:<10,} "
            f"${result.metrics.total_cost_usd:<9.4f} "
            f"{result.metrics.duration_seconds:<8.1f}s"
        )

    return True


def main():
    """Run demos."""
    print("\n" + "█" * 70)
    print(" " * 18 + "BUILD ORCHESTRATOR DEMO")
    print(" " * 15 + "AI-Powered LEGO Generation")
    print("█" * 70 + "\n")

    # Check API key
    if not check_api_key():
        print("\n⚠️  Skipping API-dependent demos")
        print("\n💡 You can still run: python3 test_orchestrator.py")
        return 1

    print("✅ API key found!")
    print(f"   Model: {config.DEFAULT_MODEL}")
    print(f"   Refinement model: {config.REFINEMENT_MODEL}")

    demos = [
        ("Simple Generation", demo_simple_generation),
        ("With Clarifications", demo_with_clarifications),
        ("Metrics Comparison", demo_metrics_comparison),
    ]

    for name, demo_func in demos:
        try:
            print(f"\n{'=' * 70}")
            print(f"Running: {name}")
            print('=' * 70)

            demo_func()

            safe_input("\nPress Enter to continue...")

        except KeyboardInterrupt:
            print("\n\n👋 Demo interrupted by user")
            return 0
        except Exception as e:
            print(f"\n❌ Demo failed: {e}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 70)
    print("✅ All demos complete!")
    print("=" * 70)

    print("\n📝 Next steps:")
    print("   1. Implement output generation (BOM, LDraw, instructions)")
    print("   2. Create CLI interface")
    print("   3. Add ASCII art preview")
    print()

    return 0


if __name__ == "__main__":
    exit(main())
