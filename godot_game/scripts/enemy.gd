extends PathFollow2D

@export var unit_id: String = "scout"
var health: int = 100
var speed: float = 150.0
var reward: int = 10
var is_dead: bool = false

func _ready() -> void:
	loop = false
	apply_balance()

func apply_balance() -> void:
	var data = ConfigManager.get_unit_data(unit_id)
	if data.is_empty():
		push_warning("Brak danych w JSON dla jednostki: " + unit_id)
		return

	health = int(data.get("hp", health))
	reward = int(data.get("reward", reward))

	var tile_size = ConfigManager.get_map_data().get("tile_size_px", 32)
	speed = float(data.get("speed", 1.0)) * tile_size

func _process(delta: float) -> void:
	progress += speed * delta
	if progress_ratio >= 1.0:
		reach_end()

func take_damage(amount: int) -> void:
	if is_dead:
		return
	health -= amount
	if health <= 0:
		die()

func reach_end() -> void:
	if is_dead:
		return
	is_dead = true
	GameManager.take_damage(1)
	queue_free()

func die() -> void:
	if is_dead:
		return
	is_dead = true
	GameManager.add_gold(reward)
	queue_free()
