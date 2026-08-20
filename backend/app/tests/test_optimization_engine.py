from app.services.optimization_engine import ScheduledOptimizationEngine
from app.services.interfaces import TransformParams


def test_next_step_increases_strength():
    engine = ScheduledOptimizationEngine(max_steps=12)
    params = TransformParams()  # step 0
    nxt = engine.next_step(params, ai_defeated=False)
    assert nxt.strength_scalar() > params.strength_scalar()


def test_step_back_decreases_strength():
    engine = ScheduledOptimizationEngine(max_steps=12)
    params = engine._params_for_step(5)
    back = engine.step_back(params)
    assert back.strength_scalar() < params.strength_scalar()


def test_step_back_never_goes_below_zero():
    engine = ScheduledOptimizationEngine(max_steps=12)
    params = TransformParams()  # already step 0
    back = engine.step_back(params)
    assert back.strength_scalar() >= 0


def test_next_step_caps_at_max():
    engine = ScheduledOptimizationEngine(max_steps=3)
    params = engine._params_for_step(3)
    nxt = engine.next_step(params, ai_defeated=False)
    # should not exceed the max_steps schedule
    assert nxt.strength_scalar() == engine._params_for_step(3).strength_scalar()


def test_human_limit_n_minus_1_backoff_sequence():
    """
    Simulates: AI defeated at step k, human still recognizes at k, k+1;
    human stops recognizing at k+2 -> locked profile should equal step k+1 (n-1).
    """
    engine = ScheduledOptimizationEngine(max_steps=12)
    params = engine._params_for_step(4)  # pretend this is where AI got defeated

    # human says recognizable twice -> push forward twice
    params = engine.next_step(params, ai_defeated=True)  # step 5
    params = engine.next_step(params, ai_defeated=True)  # step 6

    # human says NOT recognizable -> back off one (n-1 -> step 5)
    locked = engine.step_back(params)
    assert engine.step_index_from_params(locked) == 5
