extends Node
class_name WaveManager

const ENEMY_SCENE = preload("res://scenes/entities/Enemy.tscn")
@onready var spawn_timer = Timer.new()

var unit_queue: Array[String] = []
var active_path: Path2D

func _ready():
	spawn_timer.wait_time = 0.8
	spawn_timer.one_shot = false
	spawn_timer.timeout.connect(_on_spawn_timer_timeout)
	add_child(spawn_timer)

func start_custom_wave(selected_units: Array, enemy_route_node: Path2D, spawn_density: float):
	if selected_units.is_empty():
		return
		
	unit_queue = selected_units.duplicate()
	active_path = enemy_route_node
	
	spawn_timer.wait_time = spawn_density
	spawn_timer.start()
	
	print("WaveManager rozpoczął falę! Ilość: ", unit_queue.size(), ", Interwał: ", spawn_density)

func _on_spawn_timer_timeout():
	if unit_queue.is_empty():
		spawn_timer.stop()
		return
		
	var unit_type = unit_queue.pop_front()
	spawn_unit(unit_type)

func spawn_unit(unit_type_name: String):
	var enemy = ENEMY_SCENE.instantiate()
	var enemy_enum_val = GameEnums.enemyID[unit_type_name]
	enemy.unit_id = enemy_enum_val
	active_path.add_child(enemy)
