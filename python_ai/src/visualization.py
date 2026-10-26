import json

from PIL import Image, ImageDraw

def render_state(sim, filename="state.png"):
    tile_size = sim.config["map"]["tile_size_px"]
    img_width = sim.width * tile_size
    img_height = sim.height * tile_size

    img = Image.new("RGB", (img_width, img_height), "black")
    draw = ImageDraw.Draw(img, "RGBA")

    for y in range(sim.height):
        for x in range(sim.width):
            x0, y0 = x * tile_size, y * tile_size
            x1, y1 = x0 + tile_size, y0 + tile_size

            if sim.grid[y][x] == 1:
                color = (34, 139, 34)
            else:
                color = (139, 69, 19)

            draw.rectangle([x0, y0, x1, y1], fill=color, outline=(0, 0, 0))

    for tower in sim.towers:
        center_x = (tower.x * tile_size) + (tile_size / 2)
        center_y = (tower.y * tile_size) + (tile_size / 2)
        r_px = tower.range * tile_size

        draw.ellipse(
            [center_x - r_px, center_y - r_px, center_x + r_px, center_y + r_px],
            fill=(0, 0, 255, 40), outline=(0, 0, 255, 100)
        )

        tx0, ty0 = tower.x * tile_size, tower.y * tile_size
        tx1, ty1 = tx0 + tile_size, ty0 + tile_size
        draw.rectangle([tx0 + 4, ty0 + 4, tx1 - 4, ty1 - 4], fill=(0, 100, 255))

    for enemy in sim.enemies:
        ex = enemy.x * tile_size
        ey = enemy.y * tile_size

        hp_percent = max(0, enemy.hp / enemy.max_hp)

        r = 8
        draw.ellipse([ex - r, ey - r, ex + r, ey + r], fill=(255, 0, 0))

        draw.rectangle([ex - 10, ey - 12, ex + 10, ey - 9], fill=(50, 50, 50))
        draw.rectangle([ex - 10, ey - 12, ex - 10 + (20 * hp_percent), ey - 9], fill=(0, 255, 0))

    img.save(filename)


def write_state_to_file(sim, filename="state.json"):
    state = sim.to_dict()

    state.update({
        "time": sim.sim_time,
        "attacker_budget": sim.attacker_budget,
        "spawn_cooldown": sim.spawn_cooldown,
        "episode_done": sim.episode_done
    })

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=4)
