"""
Orchestrates: parse → simulate → explain.
All three steps can raise; callers handle errors.
"""
import copy

from ai.scene_parser import parse_scene_from_text
from ai.explainer import generate_explanation
from physics.simulation import run_simulation


def run_from_text(description: str) -> tuple[dict, dict, str]:
    scene = parse_scene_from_text(description)
    result = run_simulation(scene)
    explanation = generate_explanation(scene, result)
    return scene, result, explanation


def run_from_scene(scene: dict) -> tuple[dict, dict, str]:
    result = run_simulation(scene)
    explanation = generate_explanation(scene, result)
    return scene, result, explanation


def apply_changes(scene: dict, changes: dict) -> dict:
    """
    Return a modified copy of scene with changes applied.

    Top-level scalar keys (gravity, damping, duration, steps_per_second) are
    overridden directly.  Any other key is matched against object names:
        {"ball": {"mass": 5.0}, "slope": {"friction": 0.1}}
    """
    modified = copy.deepcopy(scene)

    TOP_LEVEL = {"gravity", "damping", "duration", "steps_per_second", "name"}

    for key, value in changes.items():
        if key in TOP_LEVEL:
            modified[key] = value
        else:
            # treat key as an object name
            for obj in modified.get("objects", []):
                if obj.get("name") == key and isinstance(value, dict):
                    obj.update(value)

    return modified


def run_whatif(scene: dict, changes: dict) -> tuple[dict, dict, str]:
    modified = apply_changes(scene, changes)
    return run_from_scene(modified)
