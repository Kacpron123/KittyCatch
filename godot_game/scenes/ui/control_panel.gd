extends Panel


@onready var enemy_list = $MarginContainer/VBoxContainer/ScrollContainer/EnemyList

@onready var btn_slow = $MarginContainer/VBoxContainer/HBoxContainer/BtnSlow
@onready var btn_normal = $MarginContainer/VBoxContainer/HBoxContainer/BtnNormal
@onready var btn_fast = $MarginContainer/VBoxContainer/HBoxContainer/BtnFast

@onready var btn_start = $MarginContainer/VBoxContainer/BtnStartWave

var wave_composition: Dictionary = {}
signal wave_ready_to_start(wave_queue: Array[String], density: float)

var density_speeds = {
	"slow": 0.5,
	"normal": 0.3,
	"fast": 0.1
}
var selected_density: float = 0.3

func _ready():
	btn_normal.button_pressed = true
	_generate_enemy_ui()

func _generate_enemy_ui():
	var enemy_keys = GameEnums.enemyID.keys()
	
	for i in range(enemy_keys.size()):
		var enemy_name = enemy_keys[i]
		var enemy_id = GameEnums.enemyID.values()[i]
		wave_composition[enemy_name] = 0
		var enemy_data = ConfigManager.get_enemy_data(enemy_id)
		
		var row = HBoxContainer.new()
		
		var icon = TextureRect.new()
		icon.custom_minimum_size = Vector2(40, 40)
		icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		if enemy_data.has("icon_path"):
			icon.texture = load(enemy_data["icon_path"])
		row.add_child(icon)
		
		var name_label = Label.new()
		name_label.text = enemy_name.capitalize()
		name_label.custom_minimum_size = Vector2(80, 0)
		row.add_child(name_label)
		
		var btn_minus_10 = _create_mod_button("-10", enemy_name, -10)
		var btn_minus_1 = _create_mod_button("-1", enemy_name, -1)
		
		var count_label = Label.new()
		count_label.text = "0"
		count_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		count_label.custom_minimum_size = Vector2(40, 0)
		
		count_label.add_to_group("label_" + enemy_name)
		
		var btn_plus_1 = _create_mod_button("+1", enemy_name, 1)
		var btn_plus_10 = _create_mod_button("+10", enemy_name, 10)
		
		row.add_child(btn_minus_10)
		row.add_child(btn_minus_1)
		row.add_child(count_label)
		row.add_child(btn_plus_1)
		row.add_child(btn_plus_10)
		
		enemy_list.add_child(row)

func _create_mod_button(text: String, enemy_name: String, amount: int) -> Button:
	var btn = Button.new()
	btn.text = text
	btn.custom_minimum_size = Vector2(35, 0)
	btn.pressed.connect(_on_mod_button_pressed.bind(enemy_name, amount))
	return btn

func _on_mod_button_pressed(enemy_name: String, amount: int):
	wave_composition[enemy_name] += amount
	if wave_composition[enemy_name] < 0:
		wave_composition[enemy_name] = 0
		
	var labels = get_tree().get_nodes_in_group("label_" + enemy_name)
	if labels.size() > 0:
		labels[0].text = str(wave_composition[enemy_name])

func _on_density_selected(density_key: String):
	selected_density = density_speeds[density_key]

# START WAVE
func _on_start_wave_pressed():
	var final_wave_queue: Array[String] = []
	for enemy_name in wave_composition.keys():
		var count = wave_composition[enemy_name]
		for i in range(count):
			final_wave_queue.append(enemy_name)
	final_wave_queue.shuffle()
	
	if final_wave_queue.is_empty():
		print("Fala jest pusta! Dodaj jednostki.")
		return
		
	var wave_manager = get_node("/root/LevelMaster/Managers/WaveManager") 
	var active_path = get_node("/root/LevelMaster/LevelContainer").get_child(0).get_node("EnemyRoute")
	
	wave_manager.start_custom_wave(final_wave_queue, active_path, selected_density)
	
	print("Rozpoczęto falę z prędkością: ", selected_density)
