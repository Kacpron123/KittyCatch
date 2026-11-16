extends Node
## Export authoritative map geometry and starting rules without controlling a live match.

func _ready() -> void:
	# This standalone process never sends observations or actions to the player's server.
	NetworkManager.tcp.disconnect_from_host()
	NetworkManager.set_process(false)
	var output_path = "res://.godot/training_init.json"
	var arguments = OS.get_cmdline_user_args()
	for i in range(arguments.size()):
		if arguments[i] == "--output" and i + 1 < arguments.size():
			output_path = arguments[i + 1]
		if arguments[i] == "--difficulty" and i + 1 < arguments.size():
			GameManager.selected_difficulty = arguments[i + 1]
		if arguments[i] == "--level" and i + 1 < arguments.size():
			GameManager.selected_level_path = arguments[i + 1]
	var level = load("res://scenes/core/LevelMaster.tscn").instantiate()
	get_tree().root.add_child.call_deferred(level)
	await level.ready
	var message: Dictionary = NetworkManager._pending_game_start.duplicate(true)
	if message.is_empty():
		push_error("Level did not produce a Godot init message")
		get_tree().quit(1)
		return
	var probe = load("res://scenes/entities/Tower.tscn").instantiate()
	level.get_node("Entities/Towers").add_child.call_deferred(probe)
	await probe.ready
	message["physics_probe"] = {
		"tower_scene_scale": probe.global_scale.x,
		"basic_range_world_px": probe.range_radius_px * absf(probe.global_scale.x),
		"route_length_world_px": level.active_level.get_node("EnemyRoute").curve.get_baked_length()
	}
	var file = FileAccess.open(output_path, FileAccess.WRITE)
	if file == null:
		push_error("Cannot write export: " + output_path)
		get_tree().quit(1)
		return
	file.store_string(JSON.stringify(message, "  "))
	file.close()
	print("Training init exported: ", output_path, " | map=", message.get("map_size"), " | base=", message.get("base"))
	get_tree().quit()
