"""
OptimizationEngine implementation.

This is the "n-1 iterates to the human limit" logic your spec described:

  Phase 1 (automated defeat): starting from zero degradation, step strength
    up on a fixed schedule, re-evaluating cosine similarity against the
    FaceRecognizer after each step, until similarity drops below
    settings.AI_DEFEAT_SIMILARITY_THRESHOLD ("AI defeated").

  Phase 2 (human calibration): starting from the AI-defeated step, keep
    stepping strength up and showing the frame to the human once per login
    session. As long as the human still says "recognizable", keep going.
    The instant the human says "no longer recognizable", back off one step
    (n-1) and lock that as the session's transformation_profile — maximum
    protection that's still just inside human interpretability.

This is a scheduled/greedy search rather than a trained RL policy (see the
note in the guide accompanying this codebase on why that's the right call for
a 3-day build). It sits behind the OptimizationEngine interface, so a real
trained policy can be swapped in later without touching callers.
"""
from app.services.interfaces import OptimizationEngine, TransformParams


class ScheduledOptimizationEngine(OptimizationEngine):
    """
    Increases each param roughly proportionally per step. Steps are indexed
    0..N; step 0 is "no degradation".
    """

    def __init__(self, max_steps: int = 12):
        self.max_steps = max_steps

    def _params_for_step(self, step: int) -> TransformParams:
        t = min(1.0, step / self.max_steps)
        return TransformParams(
            blur_strength=round(0.6 * t, 3),
            pixelation_strength=round(0.5 * t, 3),
            noise_strength=round(0.35 * t, 3),
            compression_quality=round(100 - 70 * t, 1),
            downsample_factor=round(1.0 - 0.5 * t, 3),
            adversarial_epsilon=round(0.8 * t, 3),
        )

    def step_index_from_params(self, params: TransformParams) -> int:
        # cheap inverse lookup by matching strength_scalar against the schedule
        best_i, best_diff = 0, float("inf")
        for i in range(self.max_steps + 1):
            diff = abs(self._params_for_step(i).strength_scalar() - params.strength_scalar())
            if diff < best_diff:
                best_i, best_diff = i, diff
        return best_i

    def next_step(self, current: TransformParams, ai_defeated: bool) -> TransformParams:
        i = self.step_index_from_params(current)
        return self._params_for_step(min(self.max_steps, i + 1))

    def step_back(self, current: TransformParams) -> TransformParams:
        i = self.step_index_from_params(current)
        return self._params_for_step(max(0, i - 1))
