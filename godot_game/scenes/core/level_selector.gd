extends Control

@onready var container = $MarginContainer/VBoxContainer/LevelContainer
@onready var btn_back = $MarginContainer/VBoxContainer/Button
@onready var difficulty_selector: OptionButton = $MarginContainer/VBoxContainer/DifficultySelector
const LEVELS_PATH = "res://scenes/levels/"

func _ready():
	var difficulties = ["hard", "medium", "easy"]
	var labels = ["Trudny", "Średni", "Łatwy"]
	for i in range(difficulties.size()):
		var difficulty: String = difficulties[i]
		difficulty_selector.add_item("%s — limit energii: %d" % [
			labels[i], GameManager.get_player_energy_limit(difficulty)
		])
		difficulty_selector.set_item_metadata(i, difficulty)
		if difficulty == GameManager.get_selected_difficulty():
			difficulty_selector.select(i)
	difficulty_selector.item_selected.connect(_on_difficulty_selected)
	load_levels()

func _on_difficulty_selected(index: int) -> void:
	GameManager.selected_difficulty = str(difficulty_selector.get_item_metadata(index))

func load_levels():
	var dir = DirAccess.open(LEVELS_PATH)
	if dir:
		for file_name in dir.get_files():
			if file_name.ends_with(".tscn") or file_name.ends_with(".tscn.remap"):
				var clean_name = file_name.replace(".remap", "")
				create_level_button(clean_name)
	else:
		push_error("Folder not Found: " + LEVELS_PATH)

func _on_back_pressed():
	get_tree().change_scene_to_file("res://scenes/core/MainMenu.tscn")
	
func create_level_button(file_name: String):
	var button = Button.new()
	button.text = file_name.replace(".tscn", "").capitalize()
	button.pressed.connect(func(): _on_level_selected(file_name))
	container.add_child(button)

func _on_level_selected(file_name: String):
	GameManager.selected_level_path = LEVELS_PATH + file_name
	get_tree().change_scene_to_file("res://scenes/core/LevelMaster.tscn")
