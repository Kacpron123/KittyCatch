extends Node2D
class_name LevelMaster

const TOWER_SCENE = preload("res://scenes/entities/Tower.tscn")

@onready var level_container = $LevelContainer
@onready var towers_container = $Entities/Towers
@onready var map_manager = $Managers/MapManager
@onready var wave_manager = $Managers/WaveManager
@onready var control_panel = $UILayer/ControlPanel

var active_level: Node2D = null

func _ready():
	if GameManager.selected_level_path != "":
		active_level = load_level(GameManager.selected_level_path)
	
	if active_level != null:
		var map_data = map_manager.generate_grid(active_level)
		
		var enemy_route = active_level.get_node("EnemyRoute")
		if not enemy_route:
			push_error("Błąd: W załadowanym poziomie brakuje węzła 'EnemyRoute'!")
		control_panel.wave_ready_to_start.connect(
			func(wave_queue: Array[String], density: float): 
				wave_manager.start_custom_wave(wave_queue, enemy_route, density)
		)
		
		NetworkManager.ai_build_command_received.connect(_on_ai_build_tower)
		var starting_ai_money = 500
		NetworkManager.send_game_start(map_data, starting_ai_money)

func load_level(level_path: String) -> Node2D:
	for child in level_container.get_children():
		child.queue_free()
		
	var level_scene = load(level_path)
	if not level_scene:
		push_error("Nie udało się załadować sceny: " + level_path)
		return null
		
	var level_instance = level_scene.instantiate()
	level_container.add_child(level_instance)
	
	print("Pomyślnie załadowano poziom: ", level_path)
	return level_instance

func _on_ai_build_tower(tower_type: GameEnums.TowerID, grid_x: int, grid_y: int):
	if map_manager.is_cell_buildable(grid_x, grid_y):
		var spawn_position = map_manager.grid_to_world(grid_x, grid_y)
		spawn_tower(tower_type, spawn_position)
		map_manager.mark_cell_occupied(grid_x, grid_y)
	else:
		print("AI próbowało zbudować wieżę na niedozwolonym polu: ", grid_x, ", ", grid_y)

func spawn_tower(tower_type: GameEnums.TowerID, pos: Vector2):
	var tower = TOWER_SCENE.instantiate()
	tower.tower_id = tower_type
	tower.position = pos
	towers_container.add_child(tower)
