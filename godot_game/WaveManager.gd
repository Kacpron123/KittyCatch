extends Node

signal wave_started(wave_index: int)
signal wave_completed(wave_index: int)
signal all_waves_completed

@export var path_2d: Path2D
@export var enemy_basic_scene: PackedScene

var waves: Array[Dictionary] = [
	{"count": 5, "interval": 1.0},
	{"count": 10, "interval": 0.8},
	{"count": 15, "interval": 0.5}
]

var current_wave_index: int = 0
var active_enemies: int = 0
var is_spawning: bool = false

func start_next_wave() -> void:
	if is_spawning or active_enemies > 0:
		print("Wave in progress, Cannot start next one!")
		return

	if current_wave_index >= waves.size():
		return

	wave_started.emit(current_wave_index)
	var wave_data = waves[current_wave_index]
	spawn_wave(wave_data["count"], wave_data["interval"])
	current_wave_index += 1

func spawn_wave(count: int, interval: float) -> void:
	is_spawning = true
	
	for i in range(count):
		spawn_enemy()
		await get_tree().create_timer(interval).timeout
	
	is_spawning = false

func spawn_enemy() -> void:
	if not enemy_basic_scene or not path_2d:
		push_warning("not enemy attached or node Path2D!")
		return

	var enemy = enemy_basic_scene.instantiate()
	
	enemy.tree_exited.connect(_on_enemy_removed)
	
	active_enemies += 1
	path_2d.add_child(enemy)

func _on_enemy_removed() -> void:
	active_enemies -= 1
	
	if not is_spawning and active_enemies <= 0:
		print("Wave ", current_wave_index, " defeated!")
		wave_completed.emit(current_wave_index)
		if current_wave_index < waves.size():
			await get_tree().create_timer(2.0).timeout
			start_next_wave()
		else:
			print("All waves finished!")
			all_waves_completed.emit()
