extends Panel


@onready var enemy_list = $MarginContainer/VBoxContainer/ScrollContainer/EnemyList

@onready var btn_slow = $MarginContainer/VBoxContainer/HBoxContainer/BtnSlow
@onready var btn_normal = $MarginContainer/VBoxContainer/HBoxContainer/BtnNormal
@onready var btn_fast = $MarginContainer/VBoxContainer/HBoxContainer/BtnFast

@onready var btn_start = $MarginContainer/VBoxContainer/BtnStartWave
@onready var wave_cost_label = $MarginContainer/VBoxContainer/WaveCostLabel

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
	btn_slow.pressed.connect(_on_density_selected.bind("slow"))
	btn_normal.pressed.connect(_on_density_selected.bind("normal"))
	btn_fast.pressed.connect(_on_density_selected.bind("fast"))
	GameManager.energy_changed.connect(_on_energy_changed)
	_generate_enemy_ui()
	_refresh_wave_cost(GameManager.energy, GameManager.max_energy)

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
		name_label.text = "%s (%d e)" % [
			enemy_name.capitalize(),
			int(enemy_data.get("energy_cost", 0))
		]
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
	_refresh_wave_cost(GameManager.energy, GameManager.max_energy)

func _on_density_selected(density_key: String):
	selected_density = density_speeds[density_key]

func _on_pause_button():
	get_tree().call_group("pause_menu", "toggle_pause")

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

	var energy_cost = _get_wave_energy_cost()
	if not GameManager.spend_energy(energy_cost):
		_refresh_wave_cost(GameManager.energy, GameManager.max_energy)
		return

	wave_ready_to_start.emit(final_wave_queue, selected_density)
	for enemy_name in wave_composition:
		wave_composition[enemy_name] = 0
		var labels = get_tree().get_nodes_in_group("label_" + enemy_name)
		if not labels.is_empty():
			labels[0].text = "0"
	_refresh_wave_cost(GameManager.energy, GameManager.max_energy)
	
	print("Rozpoczęto falę z prędkością: ", selected_density)

func _get_wave_energy_cost() -> int:
	var total_cost = 0
	for enemy_name in wave_composition:
		var enemy_id = GameEnums.enemyID.get(enemy_name, -1)
		if enemy_id < 0:
			continue
		var unit_data = ConfigManager.get_enemy_data(enemy_id)
		total_cost += wave_composition[enemy_name] * int(unit_data.get("energy_cost", 0))
	return total_cost

func _on_energy_changed(current_energy: int, max_energy: int) -> void:
	_refresh_wave_cost(current_energy, max_energy)

func _refresh_wave_cost(current_energy: int, max_energy: int) -> void:
	var energy_cost = _get_wave_energy_cost()
	wave_cost_label.text = "Wave cost: %d | Energy: %d / %d" % [energy_cost, current_energy, max_energy]
	btn_start.disabled = energy_cost <= 0 or energy_cost > current_energy
