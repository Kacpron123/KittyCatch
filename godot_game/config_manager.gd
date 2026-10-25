extends Node

var config_data: Dictionary = {}

func _ready() -> void:
	load_balance_config("res://config/balance.json")

func load_balance_config(path: String) -> void:
	if not FileAccess.file_exists(path):
		push_error("File not found at path: " + path)
		return

	var file = FileAccess.open(path, FileAccess.READ)
	var content = file.get_as_text()
	var json = JSON.new()
	var parse_result = json.parse(content)

	if parse_result == OK:
		config_data = json.data
		print("Configuration loaded succesfully!")
	else:
		push_error("Error parsing JSON in line %d: %s" % [json.get_error_line(), json.get_error_message()])

func get_unit_data(unit_name: String) -> Dictionary:
	return config_data.get("units", {}).get(unit_name, {})

func get_tower_data(tower_name: String) -> Dictionary:
	return config_data.get("towers", {}).get(tower_name, {})

func get_map_data() -> Dictionary:
	return config_data.get("map", {})
