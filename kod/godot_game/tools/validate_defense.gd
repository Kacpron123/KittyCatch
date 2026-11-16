extends Node
## Headless match against a dedicated Python endpoint, isolated from the user's game.

var level: Node2D
var schedule: Array = []
var launched: Array = []
var next_wave: int = 0
var duration: float = 120.0
var output_path: String = ""
var finished: bool = false

func _ready() -> void:
	set_process(false)
	NetworkManager.tcp.disconnect_from_host()
	var input_path = ""
	var port = 0
	var time_scale = 4.0
	var arguments = OS.get_cmdline_user_args()
	for i in range(arguments.size() - 1):
		match arguments[i]:
			"--input": input_path = arguments[i + 1]
			"--output": output_path = arguments[i + 1]
			"--port": port = int(arguments[i + 1])
			"--speed": time_scale = float(arguments[i + 1])
	if input_path.is_empty() or output_path.is_empty() or port <= 0:
		push_error("Validation requires --input, --output and a private --port")
		get_tree().quit(1)
		return
	var input: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(input_path))
	schedule = input["schedule"]
	duration = float(input["duration"])
	seed(int(input["seed"]))
	GameManager.selected_difficulty = "hard"
	GameManager.selected_level_path = "res://scenes/levels/level1.tscn"
	NetworkManager.host = "127.0.0.1"
	NetworkManager.port = port
	NetworkManager.connect_to_server()
	Engine.max_fps = 240
	Engine.physics_ticks_per_second = 240
	Engine.time_scale = time_scale
	level = load("res://scenes/core/LevelMaster.tscn").instantiate()
	get_tree().root.add_child.call_deferred(level)
	await level.ready
	get_tree().current_scene = level
	set_process(true)

func _process(_delta: float) -> void:
	if finished:
		return
	var now: float = level._elapsed_seconds
	if now >= duration or GameManager.base_health <= 0:
		finished = true
		_finish()
		return
	if not NetworkManager._is_connected or next_wave >= schedule.size():
		return
	var wave: Dictionary = schedule[next_wave]
	if now < float(wave["scheduled_time"]) or not level.wave_manager.spawn_timer.is_stopped():
		return
	if not GameManager.spend_energy(int(wave["cost"])):
		return
	var units: Array[String] = []
	for name in wave["spawn_order"]:
		units.append(str(name))
	var route: Path2D = level.active_level.get_node("EnemyRoute")
	level._on_wave_ready_to_start(units, 0.3, route)
	launched.append({"time": now, "scheduled_time": wave["scheduled_time"], "unit_types": units})
	next_wave += 1

func _finish() -> void:
	var state: Dictionary = level._build_game_state()
	NetworkManager.send_game_update(state)
	var file = FileAccess.open(output_path, FileAccess.WRITE)
	if file == null:
		push_error("Cannot save Godot validation result")
		get_tree().quit(1)
		return
	file.store_string(JSON.stringify({"final_state": state, "launched_waves": launched,
		"engine_time_scale": Engine.time_scale, "physics_ticks_per_second": Engine.physics_ticks_per_second}, "  "))
	file.close()
	print("GODOT VALIDATION | base=", GameManager.base_health, " | kills=", state.metrics.kills_total,
		" | leaks=", state.metrics.leaks_total, " | accepted=", state.metrics.ai_actions_accepted)
	await get_tree().process_frame
	get_tree().quit()
