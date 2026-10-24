import math

class Enemy:
    def __init__(self, unit_type, stats, waypoints):
        self.unit_type = unit_type
        self.hp = stats["hp"]
        self.max_hp = stats["hp"]
        self.speed = stats["speed"]
        self.reward = stats["reward"]

        self.waypoints = waypoints
        self.target_wp_idx = 1

        self.x, self.y = float(waypoints[0][0]), float(waypoints[0][1])

        self.reached_end = False

    def move(self, dt):
        if self.reached_end:
            return

        target_x, target_y = self.waypoints[self.target_wp_idx]

        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.hypot(dx, dy)

        move_dist = self.speed * dt

        if distance <= move_dist:
            self.x = target_x
            self.y = target_y
            self.target_wp_idx += 1

            if self.target_wp_idx >= len(self.waypoints):
                self.reached_end = True
        else:
            self.x += (dx / distance) * move_dist
            self.y += (dy / distance) * move_dist

    def take_damage(self, amount):
        self.hp -= amount
        return self.hp <= 0


class Tower:
    def __init__(self, x, y, tower_type, stats):
        self.x = float(x)
        self.y = float(y)
        self.tower_type = tower_type
        self.range = stats["range"]
        self.damage = stats["damage"]
        self.cooldown_time = stats["cooldown"]
        self.current_cooldown = 0.0

    def can_shoot(self):
        return self.current_cooldown <= 0

    def distance_to(self, enemy):
        return math.hypot(self.x - enemy.x, self.y - enemy.y)


class Simulator:
    def __init__(self, config_data, map_data):
        self.config = config_data
        self.map_data = map_data

        self.grid = self.map_data["grid"]
        self.waypoints = self.map_data["path"]

        self.width = self.config["map"]["width_tiles"]
        self.height = self.config["map"]["height_tiles"]

        self.gold = 150
        self.base_hp = 100
        self.enemies = []
        self.towers = []

    def build_tower(self, x, y, tower_type="basic"):
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False

        if self.grid[y][x] != 1:
            return False

        for t in self.towers:
            if int(t.x) == x and int(t.y) == y:
                return False

        stats = self.config["towers"][tower_type]
        if self.gold >= stats["cost"]:
            self.gold -= stats["cost"]
            self.towers.append(Tower(x, y, tower_type, stats))
            return True

        return False

    def spawn_enemy(self, unit_type):
        stats = self.config["units"][unit_type]
        self.enemies.append(Enemy(unit_type, stats, self.waypoints))

    def step(self, dt=0.1):
        """Wykonuje jeden logiczny krok symulacji (tick)"""

        for tower in self.towers:
            if tower.current_cooldown > 0:
                tower.current_cooldown -= dt

            if tower.can_shoot():
                for enemy in self.enemies:
                    if tower.distance_to(enemy) <= tower.range:
                        is_dead = enemy.take_damage(tower.damage)
                        tower.current_cooldown = tower.cooldown_time

                        if is_dead:
                            self.gold += enemy.reward
                            self.enemies.remove(enemy)

                        break

        for enemy in self.enemies[:]:
            enemy.move(dt)
            if enemy.reached_end:
                self.base_hp -= 1
                self.enemies.remove(enemy)
