extends Node2D

@export var damage: int = 25
@export var fire_rate: float = 1.0

@onready var turret_sprite: Sprite2D = $TurretSprite
@onready var shoot_timer: Timer = $ShootTimer
@export var projectile_scene: PackedScene

var targets: Array[Node2D] = []
var current_target: Node2D = null

func _ready() -> void:
	shoot_timer.wait_time = fire_rate
	shoot_timer.timeout.connect(_on_shoot_timer_timeout)

func _process(_delta: float) -> void:
	update_target()
	if current_target and is_instance_valid(current_target):
		turret_sprite.look_at(current_target.global_position)
		turret_sprite.rotate(90)
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
	if not projectile_scene or not is_instance_valid(current_target):
		return
	
	var proj = projectile_scene.instantiate()
	
	get_tree().current_scene.add_child(proj)
	
	proj.global_position = turret_sprite.global_position
	
	proj.setup(current_target, damage)
