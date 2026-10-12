"""Route finder for Margonem world maps.

Usage:
    from find_route import route
    result = route("Tuzmer", "Sucha Dolina")

Assumes the world directory (./world) contains one JSON file per map,
with the structure produced by the map-generation step:

    {
        "location": "<map name>",
        "destination": [
            {
                "name": "<target map>",
                "directly": true,
                "gw": {"top": <float>, "left": <float>}
            },
            {
                "name": "<indirect target>",
                "directly": false,
                "transition": [
                    {"name": "<intermediate>", "gw": {"top": <float>, "left": <float>}},
                    ...
                ],
                "gw": {"top": <float>, "left": <float>}
            },
            ...
        ],
        ...
    }

When "directly" is false, the "transition" array lists intermediate maps to
traverse.  Each transition entry's "gw" is the gateway to click on the
*previous* map in the chain to reach that intermediate map.  The outer "gw"
is the final gateway click (on the last transition map) to reach the
destination.

The "directly" field defaults to true when absent (backward compatibility).
"""

from __future__ import annotations

import json
import re
from collections import deque
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

WORLD_DIR = Path("./world")
CACHE_DIR = Path("./route_cache")


def _safe_filename(name: str) -> str:
    name = name.lower()
    for bad in '/\\:*?"<>|()':
        name = name.replace(bad, "")
    name = re.sub(r"[\s\-]+", "_", name.strip())
    name = re.sub(r"_+", "_", name).strip("_")
    return name


def _load_world(world_dir: Path) -> Tuple[Dict[str, Dict[str, Any]], Dict[Tuple[str, str], Dict]]:
    """
    Returns:
        graph  — {location: {neighbour: True}} for BFS traversal
        edges  — {(location, neighbour): edge_info} for route expansion
    """
    graph: Dict[str, Dict[str, Any]] = {}
    edges: Dict[Tuple[str, str], Dict] = {}

    if not world_dir.exists():
        raise FileNotFoundError(f"World directory not found: {world_dir}")

    for path in sorted(world_dir.glob("*.json")):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        location = data.get("location")
        if not location:
            continue
        graph[location] = {}
        for entry in data.get("destination", []) or []:
            name = entry["name"]
            gw = entry.get("gw", {})
            graph[location][name] = True
            edges[(location, name)] = {
                "gw_top": gw.get("top"),
                "gw_left": gw.get("left"),
                "directly": entry.get("directly", True),
                "transition": entry.get("transition", []),
            }

    return graph, edges


def _bfs(graph: Dict[str, Any], start: str, end: str) -> Optional[List[str]]:
    if start not in graph:
        raise ValueError(f"Unknown start location: {start!r}")
    if start == end:
        return [start]

    queue: deque = deque([(start, [start])])
    visited = {start}
    while queue:
        current, path = queue.popleft()
        for neighbour in graph.get(current, {}):
            if neighbour in visited:
                continue
            new_path = path + [neighbour]
            if neighbour == end:
                return new_path
            visited.add(neighbour)
            queue.append((neighbour, new_path))
    return None


def _expand_hop(
    here: str,
    next_map: str,
    edges: Dict[Tuple[str, str], Dict],
) -> List[Dict]:
    """Expand one logical hop into one or more flat route entries."""
    edge = edges.get((here, next_map), {})
    gw_top = edge.get("gw_top")
    gw_left = edge.get("gw_left")
    directly = edge.get("directly", True)
    transition = edge.get("transition", [])

    if directly or not transition:
        return [{"location": here, "gw_top": gw_top, "gw_left": gw_left}]

    # Indirect route: expand transition steps into flat entries.
    # Each transition entry's gw is the gateway to click on the *previous* map.
    entries: List[Dict] = []
    prev_loc = here
    for step in transition:
        step_gw = step.get("gw", {})
        entries.append({
            "location": prev_loc,
            "gw_top": step_gw.get("top"),
            "gw_left": step_gw.get("left"),
        })
        prev_loc = step["name"]
    # Final click on the last intermediate map to reach the destination
    entries.append({"location": prev_loc, "gw_top": gw_top, "gw_left": gw_left})
    return entries


def _cache_path(start: str, end: str, cache_dir: Path) -> Path:
    fname = f"route_{_safe_filename(start)}_to_{_safe_filename(end)}.json"
    return cache_dir / fname


def route(
    current_location: str,
    destination: str,
    world_dir: Path | str = WORLD_DIR,
    cache_dir: Path | str = CACHE_DIR,
    use_cache: bool = True,
) -> dict:
    """Compute (and cache) the shortest route between two maps.

    Returns a dict of the form:

        {
            "route": [
                {"location": "<from>", "gw_top": <float>, "gw_left": <float>},
                ...
            ]
        }

    Each entry represents one hop: stand on the given map and click the
    gateway at the listed coordinates to transition to the next map.
    Indirect destinations (directly: false) are expanded into multiple
    flat entries automatically.  The final destination map is not included.
    """
    world_dir = Path(world_dir)
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    cache_file = _cache_path(current_location, destination, cache_dir)
    if use_cache and cache_file.exists():
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)

    graph, edges = _load_world(world_dir)
    path = _bfs(graph, current_location, destination)
    if path is None:
        raise ValueError(f"No route from {current_location!r} to {destination!r}")

    route_entries: List[Dict] = []
    for i in range(len(path) - 1):
        here = path[i]
        next_map = path[i + 1]
        route_entries.extend(_expand_hop(here, next_map, edges))

    result = {"route": route_entries}

    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return result


def route_pretty(current_location: str, destination: str, **kwargs) -> str:
    data = route(current_location, destination, **kwargs)
    names = [hop["location"] for hop in data["route"]] + [destination]
    return " -> ".join(names)


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 3:
        start, end = sys.argv[1], sys.argv[2]
        print(route_pretty(start, end))
        print(json.dumps(route(start, end), ensure_ascii=False, indent=2))
    else:
        print("Usage: python find_route.py <from> <to>")
