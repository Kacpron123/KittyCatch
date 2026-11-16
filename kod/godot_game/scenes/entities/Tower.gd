extends Node2D

@export var tower_id: GameEnums.TowerID = GameEnums.TowerID.BASIC
@export var projectile_scene: PackedScene

@onready var turret_node: Node2D = $Turret
@onready var base_sprite: Sprite2D = $Sprite2D
@onready var turret_image: Sprite2D = $Turret/TurretSprite

@onready var shoot_timer: Timer = $ShootTimer
@onready var range_collision: CollisionShape2D = $RangeArea/CollisionShape2D

var damage: int = 15
var fire_rate: float = 1.0
var base_rotation_deg: float = 0.0
var range_radius_px: float = 96.0
var is_selected: bool = true

var targets: Array[Node2D] = []
var current_target: Node2D = null

func _ready() -> void:
	load_textures()
	apply_balance()
	shoot_timer.wait_time = fire_rate
	shoot_timer.timeout.connect(_on_shoot_timer_timeout)

func load_textures() -> void:
	var tower_name = GameEnums.TowerID.keys()[tower_id]
	
	var base_path = "res://assets/" + tower_name + "_BASE.png"
	var turret_path = "res://assets/" + tower_name + "_TURRET.png"
	
	if ResourceLoader.exists(base_path):
		base_sprite.texture = load(base_path)
	else:
		push_warning("base of tower not found: " + base_path)
		
	if ResourceLoader.exists(turret_path):
		turret_image.texture = load(turret_path)
	else:
		push_warning("turret of tower not found: " + turret_path)
		
func apply_balance() -> void:
	var data = ConfigManager.get_tower_data(tower_id)
	if data.is_empty():
		push_warning("No data in JSON for tower: " + GameEnums.TowerID.keys()[tower_id])
		return

	damage = int(data.get("damage", damage))
	fire_rate = 1.0 / maxf(float(data.get("attack_speed", 1.0)), 0.01)
	base_rotation_deg = float(data.get("rotation", 0.0))

	var tile_size = GameManager.tile_size
	var range_tiles = float(data.get("range", 3.0))
	
	# Keep the current physical reach (the tower scene is scaled to 0.4),
	# while exposing that reach explicitly in the shared training balance.
	var range_scale = float(ConfigManager.config_data.get("combat", {}).get("tower_range_scale", 0.4))
	range_radius_px = range_tiles * tile_size * range_scale / maxf(absf(global_scale.x), 0.0001)

	if range_collision and range_collision.shape is CircleShape2D:
		range_collision.shape = range_collision.shape.duplicate()
		range_collision.shape.radius = range_radius_px

	queue_redraw()
		
func _draw() -> void:
	if not is_selected:
		return

	var fill_color = Color(0.2, 0.6, 1.0, 0.15)
	draw_circle(Vector2.ZERO, range_radius_px, fill_color)

	var border_color = Color(0.2, 0.6, 1.0, 0.6)
	draw_arc(Vector2.ZERO, range_radius_px, 0.0, TAU, 64, border_color, 2.0, true)
	
func _process(_delta: float) -> void:
	update_target()

	if current_target and is_instance_valid(current_target):
		turret_node.look_at(current_target.global_position)
		if shoot_timer.is_stopped():
			shoot()
			shoot_timer.start()
	else:
		shoot_timer.stop()

func update_target() -> void:
	targets = targets.filter(func(target): return is_instance_valid(target))
	if targets.is_empty():
		current_target = null
		return
	current_target = targets[0]

func _on_range_area_area_entered(area: Area2D) -> void:
	var enemy = area.get_parent()
	if enemy.has_method("take_damage") and not targets.has(enemy):
		targets.append(enemy)

func _on_range_area_area_exited(area: Area2D) -> void:
	var enemy = area.get_parent()
	if targets.has(enemy):
		targets.erase(enemy)

func _on_shoot_timer_timeout() -> void:
	if current_target and is_instance_valid(current_target):
		shoot()

func shoot() -> void:
	if projectile_scene:
		var proj = projectile_scene.instantiate()
		get_tree().current_scene.add_child(proj)
		proj.global_position = turret_node.global_position
		proj.setup(current_target, damage)
	else:
		current_target.take_damage(damage)
