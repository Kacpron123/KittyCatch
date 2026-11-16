extends CanvasLayer

@onready var lives_bar = $Bottom/VBoxContainer/LivesProgress
@onready var lives_label = $Bottom/VBoxContainer/LivesProgress/LivesLabel
@onready var energy_bar = $Left/VBoxContainer/EnergyProgress
@onready var ai_money_label = $Bottom/VBoxContainer/AIMoneyLabel

func _ready():
	GameManager.health_changed.connect(update_lives)
	GameManager.energy_changed.connect(update_energy)
	GameManager.ai_money_changed.connect(update_ai_money)
	
	update_lives(GameManager.base_health, GameManager.max_health)
	update_energy(GameManager.energy, GameManager.max_energy)
	update_ai_money(GameManager.ai_money)

func update_lives(current_lives: int, max_lives: int):
	lives_bar.max_value = max_lives
	lives_bar.value = current_lives
	lives_label.text = str(current_lives) + " / " + str(max_lives)

func update_energy(current_energy: int, max_energy: int):
	energy_bar.max_value = max_energy
	energy_bar.value = current_energy

func update_ai_money(current_money: int) -> void:
	ai_money_label.text = "AI funds: %d" % current_money
