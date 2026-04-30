import json
import os

import ollama

from ai.prompts import EXPLAINER_SYSTEM

MODEL = "gemma4:latest"


def _build_user_prompt(scene: dict, result: dict, question: str | None) -> str:
    objects = [
        f"  {o['name']} ({o['type']})"
        for o in scene.get("objects", [])
        if o["type"] not in ("wall", "slope", "ramp")
    ]
    static = [
        f"  {o['name']} ({o['type']})"
        for o in scene.get("objects", [])
        if o["type"] in ("wall", "slope", "ramp")
    ]

    lines = [f"Scene: {scene.get('name', 'unnamed')}"]
    if objects:
        lines.append("Dynamic objects:\n" + "\n".join(objects))
    if static:
        lines.append("Static objects:\n" + "\n".join(static))

    lines.append(f"\nSimulation duration: {result['duration']}s")

    collisions = result.get("collisions", [])
    if collisions:
        c_lines = [
            f"  t={c['time']}s: {' + '.join(c['objects'])} (impulse {c['impact_impulse']} N·s)"
            for c in collisions
        ]
        lines.append("Collisions:\n" + "\n".join(c_lines))
    else:
        lines.append("Collisions: none")

    fs = result.get("final_states", {})
    if fs:
        fs_lines = []
        for name, state in fs.items():
            vx, vy = state["velocity"]
            speed = round((vx**2 + vy**2) ** 0.5, 3)
            fs_lines.append(
                f"  {name}: final pos {state['position']}, "
                f"speed {speed} m/s, peak speed {state['peak_velocity']} m/s"
            )
        lines.append("Final states:\n" + "\n".join(fs_lines))

    if question:
        lines.append(f"\nQuestion: {question}")

    return "\n".join(lines)


def _call_model(prompt: str) -> str:
    try:
        response = ollama.chat(
            model=MODEL,
            messages=[
                {"role": "system", "content": EXPLAINER_SYSTEM},
                {"role": "user", "content": prompt},
            ],
        )
    except Exception as e:
        raise RuntimeError(
            f"Could not reach Ollama ({e}).\n"
            "Make sure Ollama is running: `ollama serve`\n"
            f"And the model is available: `ollama pull {MODEL}`"
        ) from e
    return response["message"]["content"].strip()


def generate_explanation(scene: dict, result: dict) -> str:
    """Generate a plain-English explanation of the simulation result."""
    return _call_model(_build_user_prompt(scene, result, question=None))


def answer_query(scene: dict, result: dict, question: str) -> str:
    """Answer a specific question about the simulation."""
    return _call_model(_build_user_prompt(scene, result, question=question))


def check_consistency(result: dict, explanation: str) -> list[str]:
    """
    Programmatically cross-check an explanation against simulation data.
    Returns a list of discrepancy strings (empty list = no issues found).

    Checks:
    - Whether the explanation mentions/omits collision when data says otherwise
    - Whether any object names present in the result are missing from the explanation
    """
    issues = []

    collisions = result.get("collisions", [])
    has_collision = len(collisions) > 0

    lower = explanation.lower()
    mentions_collision = any(w in lower for w in ("collid", "hit", "impact", "struck", "crash"))
    mentions_no_collision = any(
        phrase in lower
        for phrase in ("no collision", "did not hit", "never hit", "does not hit",
                       "didn't hit", "no impact", "missed")
    )

    if has_collision and mentions_no_collision:
        objects = " + ".join(collisions[0]["objects"])
        t = collisions[0]["time"]
        issues.append(
            f"Explanation says no collision occurred, but simulation recorded a collision "
            f"between {objects} at t={t:.2f}s."
        )
    elif not has_collision and mentions_collision and not mentions_no_collision:
        issues.append(
            "Explanation implies a collision occurred, but simulation recorded none."
        )

    # Check that every dynamic object in the result is mentioned by name
    dynamic_names = list(result.get("final_states", {}).keys())
    for name in dynamic_names:
        if name.lower() not in lower:
            issues.append(
                f"Explanation does not mention object '{name}', which appears in the simulation result."
            )

    return issues


if __name__ == "__main__":
    import sys

    scene_path = sys.argv[1] if len(sys.argv) > 1 else "scenes/example_basic.json"
    with open(scene_path) as f:
        scene = json.load(f)

    from physics.simulation import run_simulation

    print("Running simulation...")
    result = run_simulation(scene)

    print("\n--- Explanation ---")
    print(generate_explanation(scene, result))

    queries = scene.get("queries", [])
    for q in queries:
        print(f"\nQ: {q}")
        print(f"A: {answer_query(scene, result, q)}")
