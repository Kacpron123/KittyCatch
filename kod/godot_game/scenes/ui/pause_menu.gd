extends CanvasLayer

@onready var pause_overlay = $ColorRect
@onready var window = $window # Dodane odwołanie do okna
@onready var btn_resume = $window/CenterContainer/VBoxContainer/Resume
@onready var btn_main_menu = $window/CenterContainer/VBoxContainer/BtnMainMenu

func _ready():
	add_to_group("pause_menu")
	get_tree().paused = false
	pause_overlay.hide()
	window.hide()

func _input(event):
	if event.is_action_pressed("ui_cancel", false):
		toggle_pause()
		get_viewport().set_input_as_handled()

func toggle_pause():
	var is_paused = not get_tree().paused
	get_tree().paused = is_paused
	pause_overlay.visible = is_paused
	window.visible = is_paused

func _on_main_menu_pressed():
	get_tree().paused = false 
	get_tree().change_scene_to_file("res://scenes/core/MainMenu.tscn")
