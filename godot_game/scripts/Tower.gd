extends Node2D

@export var tower_id: String = "basic"
@export var projectile_scene: PackedScene

@onready var turret_sprite: Node2D = $Turret
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
	apply_balance()
	shoot_timer.wait_time = fire_rate
	shoot_timer.timeout.connect(_on_shoot_timer_timeout)

func apply_balance() -> void:
	var data = ConfigManager.get_tower_data(tower_id)
	if data.is_empty():
		push_warning("No data in JSON for tower: " + tower_id)
		return

	damage = int(data.get("damage", damage))
	fire_rate = float(data.get("cooldown", fire_rate))
	base_rotation_deg = float(data.get("rotation", 0.0))

	var tile_size = ConfigManager.get_map_data().get("tile_size_px", 32)
	var range_tiles = float(data.get("range", 3.0))
	var range_radius_px = range_tiles * tile_size

	if range_collision and range_collision.shape is CircleShape2D:
		range_collision.shape = range_collision.shape.duplicate()
		range_collision.shape.radius = range_radius_px
		
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
		turret_sprite.look_at(current_target.global_position)
		if base_rotation_deg != 0.0:
			turret_sprite.rotate(deg_to_rad(base_rotation_deg))

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
		proj.global_position = turret_sprite.global_position
		proj.setup(current_target, damage)
	else:
		current_target.take_damage(damage)
