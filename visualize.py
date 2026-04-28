"""
Entry point for the visualization.

Usage:
  python visualize.py                          # default scene (example_basic.json)
  python visualize.py scenes/my_scene.json     # load a JSON scene file
  python visualize.py "A ball rolls down..."   # parse natural language, then visualize
"""
import json
import sys

from physics.simulation import run_simulation
from visualization.renderer import Renderer


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "scenes/example_basic.json"

    if arg.endswith(".json"):
        with open(arg) as f:
            scene = json.load(f)
        print(f"Loaded scene: {scene.get('name', arg)}")
    else:
        from ai.scene_parser import parse_scene_from_text
        print(f"Parsing: {arg!r}")
        scene = parse_scene_from_text(arg)
        print(f"Scene: {scene.get('name', '?')}")

    print("Running simulation...")
    result = run_simulation(scene)
    collisions = result["collisions"]
    print(f"Done — {len(collisions)} collision(s) recorded")
    for c in collisions:
        print(f"  {' + '.join(c['objects'])}  @ t={c['time']}s  impulse={c['impact_impulse']} N·s")

    Renderer(scene, result).run()


if __name__ == "__main__":
    main()
