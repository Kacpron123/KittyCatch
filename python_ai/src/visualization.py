import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from src.simulation import Simulation


def _snapshot(state: Simulation | dict[str, Any]) -> tuple[dict[str, Any], int]:
    if isinstance(state, Simulation):
        return state.to_dict(), int(state.tile_size)
    map_data = state.get("map", {})
    return state, int(map_data.get("cell_size_px", map_data.get("tile_size_px", 64)))


def _draw_heat_grid(
    draw: ImageDraw.ImageDraw,
    grid: list[list[int]],
    tile_size: int,
    color: tuple[int, int, int],
) -> None:
    peak = max((value for column in grid for value in column), default=0)
    if peak <= 0:
        return
    for x, column in enumerate(grid):
        for y, value in enumerate(column):
            if value <= 0:
                continue
            alpha = 45 + int(150 * value / peak)
            inset = max(2, tile_size // 8)
            draw.rectangle(
                [
                    x * tile_size + inset,
                    y * tile_size + inset,
                    (x + 1) * tile_size - inset,
                    (y + 1) * tile_size - inset,
                ],
                fill=(*color, alpha),
            )


def render_state(
    state: Simulation | dict[str, Any],
    filename: str | Path = "state.png",
) -> None:
    snapshot, tile_size = _snapshot(state)
    map_data = snapshot.get("map", {})
    grid = snapshot.get("map_grid", [])
    width = int(map_data.get("width", len(grid)))
    height = int(
        map_data.get("height", len(grid[0]) if grid else 0)
    )
    if width <= 0 or height <= 0:
        raise ValueError("Cannot render a state without map dimensions")
    tile_size = max(24, min(tile_size, 96))
    panel_width = 270
    map_width_px = width * tile_size
    map_height_px = height * tile_size
    image = Image.new("RGB", (map_width_px + panel_width, map_height_px), "#171923")
    draw = ImageDraw.Draw(image, "RGBA")

    buildable = map_data.get("buildable_grid", grid)
    route_grid = map_data.get("route_grid", [])
    cells_per_game_tile = float(
        map_data.get("game_tile_size_px", map_data.get("cell_size_px", tile_size))
    ) / max(float(map_data.get("cell_size_px", tile_size)), 1.0)
    for x in range(width):
        for y in range(height):
            value = grid[x][y] if x < len(grid) and y < len(grid[x]) else 0
            can_build = (
                x < len(buildable)
                and y < len(buildable[x])
                and buildable[x][y] == 1
            )
            color = "#405c45" if can_build else "#292d36"
            if value == 2:
                color = "#34394b"
            x0, y0 = x * tile_size, y * tile_size
            draw.rectangle(
                [x0, y0, x0 + tile_size, y0 + tile_size],
                fill=color,
                outline="#171923",
            )
            if x < len(route_grid) and y < len(route_grid[x]) and route_grid[x][y]:
                draw.rectangle(
                    [x0 + tile_size // 3, y0 + tile_size // 3,
                     x0 + 2 * tile_size // 3, y0 + 2 * tile_size // 3],
                    fill=(232, 191, 75, 180),
                )

    _draw_heat_grid(draw, map_data.get("kill_grid", []), tile_size, (240, 66, 66))
    _draw_heat_grid(draw, map_data.get("leak_grid", []), tile_size, (174, 76, 222))

    for tower in snapshot.get("towers", []):
        tx, ty = int(tower["x"]), int(tower["y"])
        center_x = (tx + 0.5) * tile_size
        center_y = (ty + 0.5) * tile_size
        radius = float(
            tower.get("range_cells", float(tower.get("range", 0)) * cells_per_game_tile)
        ) * tile_size
        draw.ellipse(
            [center_x - radius, center_y - radius, center_x + radius, center_y + radius],
            fill=(55, 119, 239, 28),
            outline=(92, 151, 255, 100),
        )
        inset = max(4, tile_size // 6)
        color = "#74a7ff" if tower.get("type") == "BASIC" else "#bd8cff"
        draw.rectangle(
            [tx * tile_size + inset, ty * tile_size + inset,
             (tx + 1) * tile_size - inset, (ty + 1) * tile_size - inset],
            fill=color,
            outline="#10131a",
        )

    for unit in snapshot.get("units", []):
        ex = (float(unit.get("grid_x", 0)) + 0.5) * tile_size
        ey = (float(unit.get("grid_y", 0)) + 0.5) * tile_size
        radius = max(5, tile_size // 6)
        enemy_color = {
            "SCOUT": "#f27b71",
            "TANK": "#e14e58",
            "SPEED": "#f1aa4b",
        }.get(unit.get("type"), "#f27b71")
        draw.ellipse(
            [ex - radius, ey - radius, ex + radius, ey + radius],
            fill=enemy_color,
            outline="#fff0e8",
        )
        bar_width = tile_size // 2
        bar_x = ex - bar_width / 2
        bar_y = ey - radius - 7
        health_ratio = max(
            0.0,
            min(1.0, float(unit.get("health_fraction", 1.0))),
        )
        draw.rectangle(
            [bar_x, bar_y, bar_x + bar_width, bar_y + 4],
            fill="#292d36",
        )
        draw.rectangle(
            [bar_x, bar_y, bar_x + bar_width * health_ratio, bar_y + 4],
            fill="#77d18a",
        )

    panel_x = map_width_px + 18
    resources = snapshot.get("resources", {})
    base = snapshot.get("base", {})
    counts = snapshot.get("counts", {})
    metrics = snapshot.get("metrics", {})
    enemies = counts.get("enemies_by_type", {})
    panel_lines = [
        ("KITTYCATCH", "#ffffff"),
        (f"Step {snapshot.get('step', 0)}  |  {snapshot.get('elapsed_seconds', 0):.1f}s", "#c5cad6"),
        ("", "#ffffff"),
        (f"AI funds: {resources.get('ai_money', snapshot.get('ai_money', 0))}", "#79b7ff"),
        (f"Player energy: {resources.get('player_energy', 0)}", "#f0d26c"),
        (f"Base HP: {base.get('health', resources.get('base_health', 0))}", "#f38c83"),
        (f"Enemy speed: {snapshot.get('enemy_speed_multiplier', 1.0):.3f}x", "#f0a45f"),
        ("", "#ffffff"),
        (f"Units alive: {sum(enemies.values())}", "#ffffff"),
    ]
    panel_lines.extend(
        (f"  {unit_type}: {amount}", "#c5cad6")
        for unit_type, amount in enemies.items()
    )
    panel_lines.extend(
        [
            ("", "#ffffff"),
            (f"Towers: {len(snapshot.get('towers', []))}", "#ffffff"),
            (f"Kills: {metrics.get('kills_total', 0)}", "#f27b71"),
            (f"Leaks: {metrics.get('leaks_total', 0)}", "#bd8cff"),
            (f"AI earned: {resources.get('ai_money_earned_total', 0)}", "#79b7ff"),
            (f"AI spent: {resources.get('ai_money_spent_total', 0)}", "#a9b5cb"),
        ]
    )
    y = 16
    for text, color in panel_lines:
        draw.text((panel_x, y), text, fill=color)
        y += 24

    Path(filename).parent.mkdir(parents=True, exist_ok=True)
    image.save(filename)


def write_state_to_file(
    state: Simulation | dict[str, Any],
    filename: str | Path = "state.json",
) -> None:
    snapshot = state.to_dict() if isinstance(state, Simulation) else state
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
