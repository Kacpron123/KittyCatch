extends Control

@onready var container = $VBoxContainer
const LEVELS_PATH = "res://scenes/levels/"

func _ready():
	load_levels()

func load_levels():
	var dir = DirAccess.open(LEVELS_PATH)
	if dir:
		for file_name in dir.get_files():
			if file_name.ends_with(".tscn") or file_name.ends_with(".tscn.remap"):
				var clean_name = file_name.replace(".remap", "")
				create_level_button(clean_name)
	else:
		push_error("Nie znaleziono folderu: " + LEVELS_PATH)

func create_level_button(file_name: String):
	var button = Button.new()
	
	button.text = file_name.replace(".tscn", "").capitalize()
	
	button.pressed.connect(func(): _on_level_selected(file_name))
	
	container.add_child(button)

func _on_level_selected(file_name: String):
	get_tree().change_scene_to_file(LEVELS_PATH + file_name)
