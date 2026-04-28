import json
import math
import os
import re

import ollama

from ai.prompts import SCENE_PARSER_SYSTEM

MODEL = "gemma4:latest"
_REQUIRED_KEYS = {"gravity", "damping", "duration", "steps_per_second", "objects"}
_VALID_TYPES = {"ball", "slope", "ramp", "block", "wall"}


def _extract_json(text: str) -> str:
    """Strip markdown fences and leading/trailing whitespace."""
    text = text.strip()
    # Remove ```json ... ``` or ``` ... ```
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _validate(scene: dict) -> list[str]:
    errors = []
    for key in _REQUIRED_KEYS:
        if key not in scene:
            errors.append(f"missing top-level key: '{key}'")
    objects = scene.get("objects", [])
    if not isinstance(objects, list) or len(objects) == 0:
        errors.append("'objects' must be a non-empty list")
    for i, obj in enumerate(objects):
        t = obj.get("type")
        if t not in _VALID_TYPES:
            errors.append(f"object[{i}] has unknown type '{t}'")
        if "name" not in obj:
            errors.append(f"object[{i}] missing 'name'")
    return errors


def _call_model(user_input: str, extra_instruction: str = "") -> str:
    prompt = user_input
    if extra_instruction:
        prompt = f"{extra_instruction}\n\n{user_input}"
    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": SCENE_PARSER_SYSTEM},
            {"role": "user", "content": prompt},
        ],
    )
    return response["message"]["content"]


def _snap_balls_to_slopes(scene: dict) -> dict:
    """
    For each ball, find any slope whose x-range contains the ball's x position
    and move the ball to sit just above that slope surface.
    This corrects the common model error of placing balls slightly inside slopes.
    """
    slopes = [o for o in scene["objects"] if o["type"] in ("slope", "ramp")]
    for obj in scene["objects"]:
        if obj["type"] != "ball":
            continue
        bx, by = obj["position"]
        radius = obj.get("radius", 0.5)
        for slope in slopes:
            sx, sy = slope["start"]
            ex, ey = slope["end"]
            x_min, x_max = min(sx, ex), max(sx, ex)
            if not (x_min <= bx <= x_max):
                continue
            # y on slope line at ball's x
            t = (bx - sx) / (ex - sx) if ex != sx else 0.0
            slope_y = sy + t * (ey - sy)
            # Perpendicular offset: raise ball by radius / cos(angle)
            dx, dy = ex - sx, ey - sy
            length = math.hypot(dx, dy)
            cos_a = abs(dx) / length if length > 0 else 1.0
            offset = radius / cos_a if cos_a > 0.1 else radius * 1.5
            target_y = slope_y + offset + 0.05  # small gap so it doesn't start embedded
            if by < target_y:
                obj["position"] = [bx, round(target_y, 3)]
    return scene


def parse_scene_from_text(user_input: str, save_to: str | None = None) -> dict:
    """
    Convert a natural language scene description to a scene dict.
    Retries once if the output is not valid JSON or fails schema validation.
    Optionally saves the result to a file path.
    """
    raw = _call_model(user_input)
    cleaned = _extract_json(raw)

    try:
        scene = json.loads(cleaned)
        errors = _validate(scene)
        if errors:
            raise ValueError(f"Schema errors: {errors}")
    except (json.JSONDecodeError, ValueError) as first_err:
        retry_instruction = (
            f"Your previous output had this problem: {first_err}. "
            "Output ONLY a valid JSON object matching the schema. No markdown, no explanation."
        )
        raw2 = _call_model(user_input, extra_instruction=retry_instruction)
        cleaned2 = _extract_json(raw2)
        scene = json.loads(cleaned2)
        errors = _validate(scene)
        if errors:
            raise ValueError(f"Scene still invalid after retry: {errors}\nRaw output:\n{raw2}")

    _snap_balls_to_slopes(scene)

    if save_to:
        os.makedirs(os.path.dirname(save_to), exist_ok=True)
        with open(save_to, "w") as f:
            json.dump(scene, f, indent=2)

    return scene


if __name__ == "__main__":
    import sys
    description = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else (
        "A heavy ball rolls down a steep ramp and hits a light block at the bottom."
    )
    print(f"Parsing: {description!r}\n")
    scene = parse_scene_from_text(description, save_to="scenes/parsed_latest.json")
    print(json.dumps(scene, indent=2))
