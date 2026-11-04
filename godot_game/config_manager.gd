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

func get_enemy_data(enemy_id: GameEnums.enemyID) -> Dictionary:
	var enemy_name: String = GameEnums.enemyID.keys()[enemy_id]
	return config_data.get("units", {}).get(enemy_name, {})

func get_tower_data(tower_id: GameEnums.TowerID) -> Dictionary:
	var tower_name: String = GameEnums.TowerID.keys()[tower_id]
	return config_data.get("towers", {}).get(tower_name, {})

func get_map_data() -> Dictionary:
	return config_data.get("map", {})
