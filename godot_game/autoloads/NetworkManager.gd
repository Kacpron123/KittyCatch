extends Node

signal connected_to_ai
signal disconnected_from_ai
signal ai_build_command_received(tower_type: int, grid_x: int, grid_y: int, command_id: String)
signal ai_command_rejected(command: Dictionary, reason: String)

const RECONNECT_INTERVAL: float = 2.0

var tcp := StreamPeerTCP.new()
var host := "127.0.0.1"
var port := 8080

var _buffer := ""
var _is_connected := false
var _reconnect_elapsed := 0.0
var _pending_game_start: Dictionary = {}
var _has_game_start := false
var _latest_game_state: Dictionary = {}
var _has_game_state := false

func _ready() -> void:
	connect_to_server()

func _process(delta: float) -> void:
	tcp.poll()
	var state = tcp.get_status()

	if state == StreamPeerTCP.STATUS_CONNECTED:
		if not _is_connected:
			_is_connected = true
			connected_to_ai.emit()
			_send_pending_game_data()

		var available_bytes = tcp.get_available_bytes()
		if available_bytes > 0:
			_process_incoming_data(tcp.get_utf8_string(available_bytes))
		return

	if _is_connected:
		_is_connected = false
		_buffer = ""
		disconnected_from_ai.emit()

	if state == StreamPeerTCP.STATUS_ERROR:
		tcp.disconnect_from_host()

	_reconnect_elapsed += delta
	if _reconnect_elapsed >= RECONNECT_INTERVAL:
		_reconnect_elapsed = 0.0
		connect_to_server()

func connect_to_server() -> void:
	_reconnect_elapsed = 0.0
	var result = tcp.connect_to_host(host, port)
	if result != OK:
		push_warning("Nie udało się rozpocząć połączenia z AI: " + error_string(result))

func _process_incoming_data(new_data: String) -> void:
	_buffer += new_data
	var messages = _buffer.split("\n")
	_buffer = messages[messages.size() - 1]

	for i in range(messages.size() - 1):
		var msg_str = messages[i].strip_edges()
		if msg_str.is_empty():
			continue

		var parsed_data = JSON.parse_string(msg_str)
		if parsed_data is Dictionary:
			_handle_message(parsed_data)
		else:
			push_error("Błąd parsowania JSON od AI: " + msg_str)

func _handle_message(message: Dictionary) -> void:
	if message.get("action", "") != "build_tower":
		if message.has("action"):
			var reason = "unsupported_action"
			push_warning("Nieobsługiwana komenda AI: " + str(message["action"]))
			ai_command_rejected.emit(message, reason)
		return

	var tower_type_value = message.get("tower_type", "")
	var tower_type := -1
	if typeof(tower_type_value) == TYPE_INT:
		tower_type = int(tower_type_value)
	elif typeof(tower_type_value) == TYPE_STRING:
		tower_type = int(GameEnums.TowerID.get(String(tower_type_value).to_upper(), -1))

	var grid_x: Variant = _parse_grid_coordinate(message.get("x"))
	var grid_y: Variant = _parse_grid_coordinate(message.get("y"))
	if (
		tower_type < 0
		or tower_type >= GameEnums.TowerID.size()
		or grid_x == null
		or grid_y == null
	):
		push_warning("AI wysłało nieprawidłową komendę budowy: " + str(message))
		ai_command_rejected.emit(message, "invalid_build_command")
		return

	ai_build_command_received.emit(
		tower_type,
		int(grid_x),
		int(grid_y),
		str(message.get("command_id", ""))
	)

func _parse_grid_coordinate(value: Variant) -> Variant:
	if typeof(value) == TYPE_INT:
		return value
	if typeof(value) != TYPE_FLOAT:
		return null

	var coordinate := float(value)
	if (
		not is_finite(coordinate)
		or coordinate != floor(coordinate)
		or coordinate < -9223372036854775808.0
		or coordinate >= 9223372036854775808.0
	):
		return null
	return int(coordinate)

func send_json(data: Dictionary) -> void:
	if tcp.get_status() != StreamPeerTCP.STATUS_CONNECTED:
		return

	var packet = JSON.stringify(data) + "\n"
	var result = tcp.put_data(packet.to_utf8_buffer())
	if result != OK:
		push_warning("Nie udało się wysłać danych do AI: " + error_string(result))

func send_game_start(
	map_grid: Array,
	map_width: int,
	map_height: int,
	unit_types: Dictionary,
	tower_types: Dictionary,
	economy: Dictionary,
	combat: Dictionary,
	buildable_grid: Array,
	route_grid: Array,
	route_points: Array,
	cell_size_px: int,
	game_tile_size_px: int,
	grid_origin_world: Vector2,
	episode_id: String
) -> void:
	_pending_game_start = {
		"protocol_version": 2,
		"type": "init",
		"episode_id": episode_id,
		"map_grid": map_grid.duplicate(true),
		"map_size": {"width": map_width, "height": map_height},
		"grid_orientation": "x_major",
		"map": {
			"buildable_grid": buildable_grid,
			"route_grid": route_grid,
			"route_points": route_points,
			"cell_size_px": cell_size_px,
			"game_tile_size_px": game_tile_size_px,
			"grid_origin_world": [grid_origin_world.x, grid_origin_world.y]
		},
		"money": GameManager.ai_money,
		"ai_money": GameManager.ai_money,
		"player": {
			"energy": GameManager.energy,
			"max_energy": GameManager.max_energy
		},
		"base": {
			"health": GameManager.base_health,
			"max_health": GameManager.max_health
		},
		"unit_types": unit_types,
		"tower_types": tower_types,
		"economy": economy,
		"combat": combat,
		"enemy_speed_multiplier": GameManager.enemy_speed_multiplier,
		"action_space": {
			"build_tower": {
				"tower_type": GameEnums.TowerID.keys(),
				"x": "zero-based grid column",
				"y": "zero-based grid row"
			}
		},
		"feature_schema": [
			"ai_money_fraction",
			"player_energy_fraction",
			"base_health_fraction",
			"enemy_speed_bonus_fraction",
			"buildable_occupancy_fraction",
			"active_scout_count",
			"active_tank_count",
			"active_speed_count",
			"basic_tower_count",
			"sniper_tower_count",
			"wave_active"
		]
	}
	_has_game_start = true
	_latest_game_state.clear()
	_has_game_state = false
	send_json(_pending_game_start)

func send_game_update(game_state: Dictionary) -> void:
	_latest_game_state = game_state.duplicate(true)
	_has_game_state = true
	send_json(_latest_game_state)

func send_unit_positions(units_data: Array) -> void:
	var game_state = _latest_game_state.duplicate(true)
	game_state["type"] = "update"
	game_state["units"] = units_data
	send_game_update(game_state)

func _send_pending_game_data() -> void:
	if _has_game_start:
		send_json(_pending_game_start)
	if _has_game_state:
		send_json(_latest_game_state)
