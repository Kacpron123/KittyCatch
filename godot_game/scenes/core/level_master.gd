extends Node2D
class_name LevelMaster

const TOWER_SCENE = preload("res://scenes/entities/Tower.tscn")

@onready var level_container = $LevelContainer
@onready var towers_container = $Entities/Towers
@onready var map_manager = $Managers/MapManager
@onready var wave_manager = $Managers/WaveManager
@onready var control_panel = $UILayer/ControlPanel

var active_level: Node2D = null
var _state_update_elapsed: float = 0.0
var _elapsed_seconds: float = 0.0
var _episode_id: String = ""
var _step: int = 0
var _event_sequence: int = 0
var _event_history: Array[Dictionary] = []
var _kill_grid: Array = []
var _leak_grid: Array = []
var _tower_grid: Array = []
var _route_grid: Array = []
var _route_points: Array = []
var _kills_by_type: Dictionary = {}
var _leaks_by_type: Dictionary = {}
var _metrics := {
	"kills_total": 0,
	"leaks_total": 0,
	"base_damage_total": 0,
	"ai_money_earned_total": 0,
	"ai_money_spent_total": 0,
	"ai_actions_accepted": 0,
	"ai_actions_rejected": 0
}

func _ready():
	add_to_group("level_master")
	_episode_id = "%d-%d" % [Time.get_unix_time_from_system(), randi()]
	for type_name in GameEnums.enemyID.keys():
		_kills_by_type[type_name] = 0
		_leaks_by_type[type_name] = 0
	var economy = ConfigManager.get_economy_data()
	var player_economy: Dictionary = economy.get("player", {})
	var ai_economy: Dictionary = economy.get("ai", {})
	var combat: Dictionary = ConfigManager.config_data.get("combat", {})
	GameManager.start_new_game(
		1000,
		int(player_economy.get("starting_energy", 40)),
		int(ai_economy.get("starting_money", 150)),
		int(player_economy.get("max_energy", 100)),
		float(player_economy.get("energy_regen_per_second", 1.0)),
		float(player_economy.get("kill_energy_refund_fraction", 0.6)),
		float(combat.get("enemy_speed_bonus_per_base_hit", 0.005)),
		float(combat.get("max_enemy_speed_bonus", 0.1))
	)

	if GameManager.selected_level_path != "":
		active_level = load_level(GameManager.selected_level_path)
	
	if active_level != null:
		var map_data = map_manager.generate_grid(active_level)
		_kill_grid = _create_empty_grid()
		_leak_grid = _create_empty_grid()
		_tower_grid = _create_empty_grid()
		
		var enemy_route = active_level.get_node_or_null("EnemyRoute")
		if enemy_route == null:
			push_error("Błąd: W załadowanym poziomie brakuje węzła 'EnemyRoute'!")
			_route_grid = _create_empty_grid()
		else:
			_route_grid = map_manager.generate_route_grid(enemy_route)
			_route_points = map_manager.get_route_points(enemy_route)
			control_panel.wave_ready_to_start.connect(
				_on_wave_ready_to_start.bind(enemy_route)
			)
		
		NetworkManager.ai_build_command_received.connect(_on_ai_build_tower)
		NetworkManager.ai_command_rejected.connect(_on_ai_command_rejected)
		NetworkManager.send_game_start(
			map_data,
			map_manager.map_width,
			map_manager.map_height,
			ConfigManager.config_data.get("units", {}),
			ConfigManager.config_data.get("towers", {}),
			economy,
			combat,
			map_manager.buildable_grid,
			_route_grid,
			_route_points,
			map_manager.get_cell_size_px(),
			GameManager.tile_size,
			map_manager.grid_to_world(0, 0),
			_episode_id
		)

func _process(delta: float) -> void:
	if active_level == null:
		return

	_elapsed_seconds += delta
	_state_update_elapsed += delta
	if _state_update_elapsed >= 0.5:
		_state_update_elapsed = 0.0
		NetworkManager.send_game_update(_build_game_state())

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

func _on_wave_ready_to_start(
	wave_queue: Array[String],
	density: float,
	enemy_route: Path2D
) -> void:
	wave_manager.start_custom_wave(wave_queue, enemy_route, density)
	NetworkManager.send_game_update(_build_game_state())

func _on_ai_build_tower(
	tower_type: int,
	grid_x: int,
	grid_y: int,
	command_id: String
) -> void:
	if tower_type < 0 or tower_type >= GameEnums.TowerID.size():
		push_warning("AI wybrało nieznany typ wieży: " + str(tower_type))
		_record_ai_action(false, "unknown_tower_type", tower_type, grid_x, grid_y, 0, command_id)
		return
	if not map_manager.is_cell_buildable(grid_x, grid_y):
		push_warning("AI próbowało zbudować wieżę na niedozwolonym polu: %d, %d" % [grid_x, grid_y])
		_record_ai_action(false, "cell_not_buildable", tower_type, grid_x, grid_y, 0, command_id)
		return

	var tower_data = ConfigManager.get_tower_data(tower_type)
	var tower_cost = int(tower_data.get("cost", -1))
	if tower_cost < 0:
		push_error("Brak prawidłowego kosztu wieży: " + GameEnums.TowerID.keys()[tower_type])
		_record_ai_action(false, "invalid_tower_cost", tower_type, grid_x, grid_y, tower_cost, command_id)
		return
	if not GameManager.spend_ai_money(tower_cost):
		push_warning("AI nie ma wystarczająco pieniędzy na tę wieżę.")
		_record_ai_action(false, "insufficient_funds", tower_type, grid_x, grid_y, tower_cost, command_id)
		return

	var spawn_position = map_manager.grid_to_world(grid_x, grid_y)
	spawn_tower(tower_type, spawn_position)
	map_manager.mark_cell_occupied(grid_x, grid_y)
	_tower_grid[grid_x][grid_y] = tower_type + 1
	_record_ai_action(true, "built", tower_type, grid_x, grid_y, tower_cost, command_id)

func spawn_tower(tower_type: GameEnums.TowerID, pos: Vector2) -> void:
	var tower = TOWER_SCENE.instantiate()
	tower.tower_id = tower_type
	towers_container.add_child(tower)
	tower.global_position = pos

func _build_game_state() -> Dictionary:
	_step += 1
	var units: Array[Dictionary] = []
	for enemy in get_tree().get_nodes_in_group("enemies"):
		if not is_instance_valid(enemy):
			continue
		var unit_position: Vector2 = enemy.global_position
		var grid_position = map_manager.world_to_grid(unit_position)
		units.append({
			"type": GameEnums.enemyID.keys()[enemy.unit_id],
			"type_id": enemy.unit_id,
			"health": enemy.health,
			"max_health": enemy.max_health,
			"health_fraction": float(enemy.health) / maxf(float(enemy.max_health), 1.0),
			"progress": enemy.progress_ratio,
			"speed": enemy.speed * GameManager.enemy_speed_multiplier,
			"grid_x": grid_position.x,
			"grid_y": grid_position.y,
			"x": roundi(unit_position.x),
			"y": roundi(unit_position.y)
		})

	var towers: Array[Dictionary] = []
	for tower in towers_container.get_children():
		var grid_position = map_manager.world_to_grid(tower.global_position)
		var tower_data = ConfigManager.get_tower_data(tower.tower_id)
		var target_progress = -1.0
		if is_instance_valid(tower.current_target):
			target_progress = tower.current_target.progress_ratio
		towers.append({
			"type": GameEnums.TowerID.keys()[tower.tower_id],
			"type_id": tower.tower_id,
			"x": grid_position.x,
			"y": grid_position.y,
			"damage": tower.damage,
			"range": float(tower_data.get("range", 0.0)),
			"attack_speed": float(tower_data.get("attack_speed", 0.0)),
			"target_progress": target_progress
		})

	var metrics = _metrics.duplicate(true)
	metrics["kills_by_type"] = _kills_by_type.duplicate(true)
	metrics["leaks_by_type"] = _leaks_by_type.duplicate(true)

	var enemies_by_type := {}
	var towers_by_type := {}
	for type_name in GameEnums.enemyID.keys():
		enemies_by_type[type_name] = 0
		_kills_by_type[type_name] = _kills_by_type.get(type_name, 0)
		_leaks_by_type[type_name] = _leaks_by_type.get(type_name, 0)
	for type_name in GameEnums.TowerID.keys():
		towers_by_type[type_name] = 0
	for unit in units:
		enemies_by_type[unit["type"]] += 1
	for tower in towers:
		towers_by_type[tower["type"]] += 1

	var total_buildable = 0
	for column in map_manager.buildable_grid:
		for cell in column:
			if cell == 1:
				total_buildable += 1
	var money_fraction = float(GameManager.ai_money) / maxf(
		float(GameManager.ai_money + _metrics.ai_money_spent_total),
		1.0
	)
	var energy_fraction = float(GameManager.energy) / maxf(float(GameManager.max_energy), 1.0)
	var health_fraction = float(GameManager.base_health) / maxf(float(GameManager.max_health), 1.0)
	var speed_bonus_fraction = (GameManager.enemy_speed_multiplier - 1.0) / maxf(
		GameManager.max_enemy_speed_bonus,
		0.0001
	)
	var occupancy_fraction = float(towers.size()) / maxf(float(total_buildable), 1.0)
	var wave_active = not wave_manager.spawn_timer.is_stopped()
	var feature_vector: Array[float] = [
		money_fraction,
		energy_fraction,
		health_fraction,
		speed_bonus_fraction,
		occupancy_fraction,
		float(enemies_by_type["SCOUT"]),
		float(enemies_by_type["TANK"]),
		float(enemies_by_type["SPEED"]),
		float(towers_by_type["BASIC"]),
		float(towers_by_type["SNIPER"]),
		1.0 if wave_active else 0.0
	]

	return {
		"protocol_version": 2,
		"type": "update",
		"episode_id": _episode_id,
		"step": _step,
		"elapsed_seconds": _elapsed_seconds,
		"map_grid": map_manager.grid_data,
		"ai_money": GameManager.ai_money,
		"enemy_speed_multiplier": GameManager.enemy_speed_multiplier,
		"resources": {
			"ai_money": GameManager.ai_money,
			"ai_money_earned_total": _metrics.ai_money_earned_total,
			"ai_money_spent_total": _metrics.ai_money_spent_total,
			"player_energy": GameManager.energy,
			"player_max_energy": GameManager.max_energy,
			"base_health": GameManager.base_health,
			"base_max_health": GameManager.max_health
		},
		"player": {
			"energy": GameManager.energy,
			"max_energy": GameManager.max_energy
		},
		"base": {
			"health": GameManager.base_health,
			"max_health": GameManager.max_health
		},
		"wave": {
			"active": wave_active,
			"queued_units": wave_manager.unit_queue,
			"queued_count": wave_manager.unit_queue.size(),
			"active_unit_count": units.size(),
			"spawn_interval": wave_manager.spawn_timer.wait_time,
			"spawn_time_left": wave_manager.spawn_timer.time_left
		},
		"terminal": GameManager.base_health <= 0,
		"map": {
			"width": map_manager.map_width,
			"height": map_manager.map_height,
			"orientation": "x_major",
			"cell_size_px": map_manager.get_cell_size_px(),
			"game_tile_size_px": GameManager.tile_size,
			"grid_origin_world": [
				map_manager.grid_to_world(0, 0).x,
				map_manager.grid_to_world(0, 0).y
			],
			"buildable_grid": map_manager.buildable_grid,
			"available_buildable_cells": total_buildable - towers.size(),
			"route_grid": _route_grid,
			"tower_type_grid": _tower_grid,
			"kill_grid": _kill_grid,
			"leak_grid": _leak_grid
		},
		"units": units,
		"towers": towers,
		"counts": {
			"enemies_by_type": enemies_by_type,
			"towers_by_type": towers_by_type
		},
		"metrics": metrics,
		"events": _event_history.duplicate(true),
		"features": {
			"ai_money_fraction": money_fraction,
			"player_energy_fraction": energy_fraction,
			"base_health_fraction": health_fraction,
			"enemy_speed_bonus_fraction": speed_bonus_fraction,
			"buildable_occupancy_fraction": occupancy_fraction
		},
		"feature_vector": feature_vector
	}

func record_enemy_killed(enemy: Node2D, energy_refund: int) -> void:
	var enemy_type = GameEnums.enemyID.keys()[enemy.unit_id]
	var cell = map_manager.world_to_grid(enemy.global_position)
	_increment_grid_cell(_kill_grid, cell)
	_metrics.kills_total += 1
	_metrics.ai_money_earned_total += enemy.ai_reward
	_kills_by_type[enemy_type] = _kills_by_type.get(enemy_type, 0) + 1
	_record_event({
		"kind": "unit_killed",
		"unit_type": enemy_type,
		"grid_x": cell.x,
		"grid_y": cell.y,
		"world_x": roundi(enemy.global_position.x),
		"world_y": roundi(enemy.global_position.y),
		"ai_money_earned": enemy.ai_reward,
		"player_energy_refunded": energy_refund
	})

func record_enemy_leaked(enemy: Node2D) -> void:
	var enemy_type = GameEnums.enemyID.keys()[enemy.unit_id]
	var cell = map_manager.world_to_grid(enemy.global_position)
	_increment_grid_cell(_leak_grid, cell)
	_metrics.leaks_total += 1
	_metrics.base_damage_total += 1
	_leaks_by_type[enemy_type] = _leaks_by_type.get(enemy_type, 0) + 1
	_record_event({
		"kind": "base_damaged",
		"unit_type": enemy_type,
		"grid_x": cell.x,
		"grid_y": cell.y,
		"world_x": roundi(enemy.global_position.x),
		"world_y": roundi(enemy.global_position.y),
		"base_damage": 1,
		"enemy_speed_multiplier": GameManager.enemy_speed_multiplier
	})

func _record_ai_action(
	accepted: bool,
	reason: String,
	tower_type: int,
	grid_x: int,
	grid_y: int,
	cost: int,
	command_id: String
) -> void:
	var metric_name = "ai_actions_accepted" if accepted else "ai_actions_rejected"
	_metrics[metric_name] += 1
	if accepted:
		_metrics.ai_money_spent_total += cost
	_record_event({
		"kind": "action_result",
		"accepted": accepted,
		"reason": reason,
		"tower_type": GameEnums.TowerID.keys()[tower_type] if tower_type >= 0 and tower_type < GameEnums.TowerID.size() else "UNKNOWN",
		"grid_x": grid_x,
		"grid_y": grid_y,
		"cost": cost,
		"command_id": command_id
	})
	NetworkManager.send_game_update(_build_game_state())

func _on_ai_command_rejected(command: Dictionary, reason: String) -> void:
	_metrics.ai_actions_rejected += 1
	_record_event({
		"kind": "action_result",
		"action": str(command.get("action", "build_tower")),
		"accepted": false,
		"reason": reason,
		"tower_type": str(command.get("tower_type", "UNKNOWN")),
		"grid_x": int(command.get("x", -1)) if typeof(command.get("x", -1)) == TYPE_INT else -1,
		"grid_y": int(command.get("y", -1)) if typeof(command.get("y", -1)) == TYPE_INT else -1,
		"command_id": str(command.get("command_id", ""))
	})
	NetworkManager.send_game_update(_build_game_state())

func _record_event(event: Dictionary) -> void:
	_event_sequence += 1
	event["event_id"] = "%s:%d" % [_episode_id, _event_sequence]
	event["step"] = _step
	event["elapsed_seconds"] = _elapsed_seconds
	_event_history.append(event)
	if _event_history.size() > 128:
		_event_history.pop_front()

func _create_empty_grid() -> Array:
	var grid: Array = []
	for x in range(map_manager.map_width):
		var column: Array[int] = []
		column.resize(map_manager.map_height)
		column.fill(0)
		grid.append(column)
	return grid

func _increment_grid_cell(grid: Array, cell: Vector2i) -> void:
	if cell.x >= 0 and cell.x < map_manager.map_width and cell.y >= 0 and cell.y < map_manager.map_height:
		grid[cell.x][cell.y] += 1
