"""
Build Orchestrator - Coordinates the full AI-powered generation workflow.

This module coordinates:
1. Prompt clarification and enrichment
2. LLM-based build generation
3. Physical validation
4. Iterative refinement with user confirmation
5. Metrics tracking (tokens, cost, time)
6. Progress reporting

Architecture decisions implemented:
- Smart defaults + confirmation for user interaction
- Interactive clarification for ambiguous prompts
- LLM-driven refinement with full context
- Unlimited iterations with user confirmation
- Show partial progress when validation fails
"""

import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

from lego_architect.core.data_structures import BuildState
from lego_architect.llm import LLMEngine
from lego_architect.validation import PhysicalValidator


@dataclass
class BuildMetrics:
    """Metrics for a build generation session."""

    # Timing
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    duration_seconds: float = 0.0

    # Token usage
    total_tokens: int = 0
    cached_tokens: int = 0
    generation_tokens: int = 0
    refinement_tokens: int = 0

    # Costs (estimated)
    total_cost_usd: float = 0.0
    generation_cost_usd: float = 0.0
    refinement_cost_usd: float = 0.0

    # Iterations
    generation_iterations: int = 0
    refinement_iterations: int = 0
    total_iterations: int = 0

    # Validation
    validation_errors_found: int = 0
    validation_errors_fixed: int = 0

    # Build stats
    final_part_count: int = 0
    final_dimensions: Tuple[int, int, int] = (0, 0, 0)

    def finish(self):
        """Mark metrics as complete."""
        self.end_time = time.time()
        self.duration_seconds = self.end_time - self.start_time
        self.total_iterations = self.generation_iterations + self.refinement_iterations

    def add_llm_result(self, result, is_refinement: bool = False):
        """Add metrics from an LLM result."""
        self.total_tokens += result.tokens_used
        self.cached_tokens += result.cached_tokens

        # Estimate costs
        # Sonnet 4: $3/M input, $15/M output (assume 1:2 ratio)
        # Haiku 3.5: $1/M input, $5/M output
        input_tokens = result.tokens_used * 0.67  # Rough estimate
        output_tokens = result.tokens_used * 0.33

        if is_refinement:
            # Haiku pricing
            cost = (input_tokens * 1.0 / 1_000_000) + (output_tokens * 5.0 / 1_000_000)
            self.refinement_cost_usd += cost
            self.refinement_tokens += result.tokens_used
            self.refinement_iterations += 1
        else:
            # Sonnet pricing
            cost = (input_tokens * 3.0 / 1_000_000) + (output_tokens * 15.0 / 1_000_000)
            self.generation_cost_usd += cost
            self.generation_tokens += result.tokens_used
            self.generation_iterations += 1

        self.total_cost_usd = self.generation_cost_usd + self.refinement_cost_usd

    def __str__(self) -> str:
        """Format metrics for display."""
        return f"""Build Metrics:
  Duration: {self.duration_seconds:.1f}s
  Iterations: {self.total_iterations} ({self.generation_iterations} generation, {self.refinement_iterations} refinement)
  Tokens: {self.total_tokens:,} (cached: {self.cached_tokens:,})
  Cost: ${self.total_cost_usd:.4f} (generation: ${self.generation_cost_usd:.4f}, refinement: ${self.refinement_cost_usd:.4f})
  Parts: {self.final_part_count}
  Dimensions: {self.final_dimensions[0]}×{self.final_dimensions[1]} studs, {self.final_dimensions[2]} plates tall
  Errors found: {self.validation_errors_found}
  Errors fixed: {self.validation_errors_fixed}"""


@dataclass
class BuildResult:
    """Result of orchestrated build generation."""

    success: bool
    build_state: BuildState
    metrics: BuildMetrics
    validation_result: Optional[object] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    user_cancelled: bool = False


@dataclass
class PromptClarification:
    """Clarification for an ambiguous prompt."""

    question: str
    suggestions: List[str]
    default: Optional[str] = None


# Type alias for progress callback
ProgressCallback = Callable[[str, Dict], None]


class BuildOrchestrator:
    """
    Coordinates the full build generation workflow.

    This orchestrator:
    1. Clarifies ambiguous prompts with smart defaults
    2. Generates builds using LLM Engine
    3. Validates physical correctness
    4. Refines builds through unlimited iterations (with user confirmation)
    5. Tracks comprehensive metrics
    6. Provides progress updates via callbacks
    """

    def __init__(
        self,
        llm_engine: Optional[LLMEngine] = None,
        validator: Optional[PhysicalValidator] = None,
        progress_callback: Optional[ProgressCallback] = None,
    ):
        """
        Initialize orchestrator.

        Args:
            llm_engine: LLM engine instance (creates if not provided)
            validator: Physical validator instance (creates if not provided)
            progress_callback: Optional callback for progress updates
                               Signature: callback(stage: str, data: Dict)
        """
        self.llm_engine = llm_engine or LLMEngine()
        self.validator = validator or PhysicalValidator()
        self.progress_callback = progress_callback

    def _report_progress(self, stage: str, **data):
        """Report progress to callback if provided."""
        if self.progress_callback:
            self.progress_callback(stage, data)

    def clarify_prompt(self, user_prompt: str) -> Tuple[str, List[PromptClarification]]:
        """
        Analyze prompt and identify clarifications needed.

        Returns:
            Tuple of (enriched_prompt, clarifications_needed)
        """
        clarifications = []

        # Check for size specification
        size_keywords = ["small", "medium", "large", "tiny", "huge"]
        has_size = any(word in user_prompt.lower() for word in size_keywords)

        if not has_size:
            clarifications.append(
                PromptClarification(
                    question="What size should the build be?",
                    suggestions=["Small (10-30 parts)", "Medium (50-100 parts)", "Large (150+ parts)"],
                    default="Medium (50-100 parts)",
                )
            )

        # Check for color specification
        color_keywords = ["red", "blue", "green", "yellow", "white", "black", "gray"]
        has_color = any(word in user_prompt.lower() for word in color_keywords)

        if not has_color:
            clarifications.append(
                PromptClarification(
                    question="What color scheme should be used?",
                    suggestions=["Let AI decide", "Primarily red", "Primarily blue", "Mixed colors"],
                    default="Let AI decide",
                )
            )

        # Check for style specification (for certain objects)
        style_objects = ["house", "building", "castle", "spaceship", "car", "ship"]
        has_style_object = any(obj in user_prompt.lower() for obj in style_objects)

        if has_style_object and "style" not in user_prompt.lower():
            clarifications.append(
                PromptClarification(
                    question="What style should it be?",
                    suggestions=["Simple/minimalist", "Detailed/realistic", "Creative/artistic"],
                    default="Simple/minimalist",
                )
            )

        return user_prompt, clarifications

    def enrich_prompt(
        self, user_prompt: str, clarifications: Dict[str, str]
    ) -> str:
        """
        Enrich user prompt with clarification answers.

        Args:
            user_prompt: Original user prompt
            clarifications: Dict mapping questions to answers

        Returns:
            Enriched prompt for LLM
        """
        enriched = user_prompt

        # Add clarifications as additional context
        if clarifications:
            enriched += "\n\nAdditional requirements:"
            for question, answer in clarifications.items():
                # Extract key requirement from question and answer
                if "size" in question.lower():
                    enriched += f"\n- Size: {answer}"
                elif "color" in question.lower() and answer != "Let AI decide":
                    enriched += f"\n- Color: {answer}"
                elif "style" in question.lower():
                    enriched += f"\n- Style: {answer}"

        return enriched

    def generate_build(
        self,
        prompt: str,
        build_name: Optional[str] = None,
        auto_clarify: bool = True,
        clarifications: Optional[Dict[str, str]] = None,
        max_refinement_iterations: int = 5,
        auto_confirm_refinement: bool = False,
        refinement_callback: Optional[Callable[[BuildState, List[str], int], bool]] = None,
    ) -> BuildResult:
        """
        Generate a LEGO build from natural language prompt.

        Args:
            prompt: Natural language description
            build_name: Optional name for the build
            auto_clarify: If True, use smart defaults for clarifications
            clarifications: Pre-answered clarifications (skips clarification step)
            max_refinement_iterations: Maximum refinement attempts
            auto_confirm_refinement: If True, automatically continue refinement
            refinement_callback: Called before each refinement, return False to stop
                                Signature: callback(build_state, errors, iteration) -> continue

        Returns:
            BuildResult with build, metrics, and status
        """
        metrics = BuildMetrics()
        build_state = BuildState(name=build_name or "AI Generated Build", prompt=prompt)

        self._report_progress("start", prompt=prompt)

        # Step 1: Prompt clarification
        enriched_prompt = prompt

        if clarifications is None and not auto_clarify:
            _, needed_clarifications = self.clarify_prompt(prompt)

            if needed_clarifications:
                self._report_progress(
                    "clarification_needed", clarifications=needed_clarifications
                )
                # In interactive mode, this would wait for user input
                # For now, we'll use defaults
                clarifications = {}

        if clarifications:
            enriched_prompt = self.enrich_prompt(prompt, clarifications)
            self._report_progress("prompt_enriched", enriched_prompt=enriched_prompt)

        # Step 2: Initial generation
        self._report_progress("generation_start", iteration=1)

        try:
            result = self.llm_engine.generate_build(enriched_prompt, build_state)
            metrics.add_llm_result(result, is_refinement=False)

            self._report_progress(
                "generation_complete",
                iteration=1,
                parts_count=len(build_state.parts),
                tokens=result.tokens_used,
            )

        except Exception as e:
            self._report_progress("generation_error", error=str(e))
            metrics.finish()
            return BuildResult(
                success=False,
                build_state=build_state,
                metrics=metrics,
                errors=[f"Generation failed: {str(e)}"],
            )

        # Step 3: Validation
        self._report_progress("validation_start")

        validation = self.validator.validate_build(build_state)

        self._report_progress(
            "validation_complete",
            is_valid=validation.is_valid,
            error_count=len(validation.errors),
        )

        if validation.is_valid:
            metrics.finish()
            metrics.final_part_count = len(build_state.parts)
            metrics.final_dimensions = build_state.get_dimensions()

            self._report_progress("success", metrics=metrics)

            return BuildResult(
                success=True,
                build_state=build_state,
                metrics=metrics,
                validation_result=validation,
            )

        # Step 4: Refinement loop
        metrics.validation_errors_found = len(validation.errors)
        errors_at_start = len(validation.errors)

        for iteration in range(1, max_refinement_iterations + 1):
            self._report_progress(
                "refinement_needed",
                iteration=iteration,
                error_count=len(validation.errors),
                errors=validation.errors[:3],  # Show first 3
            )

            # Check if user wants to continue
            if refinement_callback:
                should_continue = refinement_callback(
                    build_state, validation.errors, iteration
                )

                if not should_continue:
                    self._report_progress("refinement_cancelled", iteration=iteration)
                    metrics.finish()
                    metrics.final_part_count = len(build_state.parts)
                    metrics.final_dimensions = build_state.get_dimensions()

                    return BuildResult(
                        success=False,
                        build_state=build_state,
                        metrics=metrics,
                        validation_result=validation,
                        errors=validation.errors,
                        user_cancelled=True,
                    )

            elif not auto_confirm_refinement:
                # In non-auto mode, would prompt user here
                # For now, continue automatically
                pass

            # Attempt refinement
            self._report_progress("refinement_start", iteration=iteration)

            try:
                result = self.llm_engine.refine_build(
                    build_state, validation.errors, iteration
                )
                metrics.add_llm_result(result, is_refinement=True)

                self._report_progress(
                    "refinement_complete",
                    iteration=iteration,
                    parts_count=len(build_state.parts),
                    tokens=result.tokens_used,
                )

            except Exception as e:
                self._report_progress("refinement_error", error=str(e), iteration=iteration)
                metrics.finish()
                return BuildResult(
                    success=False,
                    build_state=build_state,
                    metrics=metrics,
                    validation_result=validation,
                    errors=[f"Refinement failed: {str(e)}"],
                )

            # Re-validate
            self._report_progress("validation_start", iteration=iteration)
            validation = self.validator.validate_build(build_state)

            self._report_progress(
                "validation_complete",
                iteration=iteration,
                is_valid=validation.is_valid,
                error_count=len(validation.errors),
            )

            if validation.is_valid:
                metrics.validation_errors_fixed = errors_at_start - len(validation.errors)
                metrics.finish()
                metrics.final_part_count = len(build_state.parts)
                metrics.final_dimensions = build_state.get_dimensions()

                self._report_progress("success", metrics=metrics, iterations=iteration)

                return BuildResult(
                    success=True,
                    build_state=build_state,
                    metrics=metrics,
                    validation_result=validation,
                )

        # Max iterations reached
        metrics.validation_errors_fixed = errors_at_start - len(validation.errors)
        metrics.finish()
        metrics.final_part_count = len(build_state.parts)
        metrics.final_dimensions = build_state.get_dimensions()

        self._report_progress(
            "max_iterations_reached",
            max_iterations=max_refinement_iterations,
            remaining_errors=len(validation.errors),
        )

        return BuildResult(
            success=False,
            build_state=build_state,
            metrics=metrics,
            validation_result=validation,
            errors=validation.errors,
            warnings=[f"Max refinement iterations ({max_refinement_iterations}) reached"],
        )

    def generate_build_interactive(
        self,
        prompt: str,
        build_name: Optional[str] = None,
        user_input_callback: Optional[Callable[[str, List[str]], str]] = None,
    ) -> BuildResult:
        """
        Generate build with full interactive mode.

        This method handles:
        - Prompt clarification with user input
        - Refinement confirmation at each iteration
        - Progress display

        Args:
            prompt: Natural language description
            build_name: Optional name for the build
            user_input_callback: Callback for user input
                                Signature: callback(question, options) -> answer

        Returns:
            BuildResult with build, metrics, and status
        """

        def refinement_callback(build_state, errors, iteration):
            """Ask user if they want to continue refinement."""
            if user_input_callback:
                question = (
                    f"Iteration {iteration}: Found {len(errors)} validation errors. "
                    f"Continue refinement?"
                )
                answer = user_input_callback(question, ["Yes", "No", "Show errors"])

                if answer == "Show errors":
                    # Show errors and ask again
                    for i, error in enumerate(errors[:5], 1):
                        print(f"  {i}. {error}")
                    answer = user_input_callback("Continue refinement?", ["Yes", "No"])

                return answer == "Yes"

            return True  # Auto-continue if no callback

        # Get clarifications
        _, clarifications_needed = self.clarify_prompt(prompt)
        clarifications = {}

        if clarifications_needed and user_input_callback:
            for clarification in clarifications_needed:
                answer = user_input_callback(
                    clarification.question, clarification.suggestions
                )
                clarifications[clarification.question] = answer

        return self.generate_build(
            prompt=prompt,
            build_name=build_name,
            clarifications=clarifications,
            max_refinement_iterations=999,  # Unlimited with user confirmation
            refinement_callback=refinement_callback,
        )
