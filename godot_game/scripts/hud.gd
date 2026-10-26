extends CanvasLayer

@onready var gold_label: Label = $MarginContainer/HBoxContainer/GoldLabel
@onready var health_label: Label = $MarginContainer/HBoxContainer/HealthLabel

func _ready() -> void:
	GameManager.gold_changed.connect(_update_gold_display)
	GameManager.health_changed.connect(_update_health_display)
	
	_update_gold_display(GameManager.gold)
	_update_health_display(GameManager.base_health)

func _update_gold_display(amount: int) -> void:
	gold_label.text = "💰 Gold: %d" % amount

func _update_health_display(current_health: int) -> void:
	health_label.text = "❤️ Healt: %d" % current_health
