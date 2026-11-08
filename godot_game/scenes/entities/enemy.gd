extends PathFollow2D

@export var path_spread: float = 8.0
@export var unit_id: GameEnums.enemyID = GameEnums.enemyID.SCOUT
var health: int = 20
var max_health: int = 20
var speed: float = 1.0
var ai_reward: int = 5
var energy_cost: int = 0
var is_dead: bool = false

func _ready() -> void:
	add_to_group("enemies")
	loop = false
	apply_balance()
	v_offset = randf_range(-path_spread, path_spread)

func apply_balance() -> void:
	var data = ConfigManager.get_enemy_data(unit_id)
	if data.is_empty():
		push_warning("No data in JSON for enemy: " + GameEnums.enemyID.keys()[unit_id])
		return

	health = int(data.get("hp", health))
	max_health = health
	ai_reward = int(data.get("ai_reward", ai_reward))
	energy_cost = int(data.get("energy_cost", energy_cost))

	var tile_size = GameManager.tile_size
	speed = float(data.get("speed", 1.0)) * tile_size

func _process(delta: float) -> void:
	progress += speed * GameManager.enemy_speed_multiplier * delta
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
	var level_master = get_tree().current_scene
	if level_master and level_master.has_method("record_enemy_leaked"):
		level_master.record_enemy_leaked(self)
	queue_free()

func die() -> void:
	if is_dead:
		return
	is_dead = true
	var energy_refund = floori(energy_cost * GameManager.kill_energy_refund_fraction)
	GameManager.add_energy(energy_refund)
	GameManager.add_ai_money(ai_reward)
	var level_master = get_tree().current_scene
	if level_master and level_master.has_method("record_enemy_killed"):
		level_master.record_enemy_killed(self, energy_refund)
	queue_free()
