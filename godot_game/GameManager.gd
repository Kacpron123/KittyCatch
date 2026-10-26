extends Node

signal gold_changed(new_amount: int)
signal health_changed(new_health: int)
signal game_over

@export var starting_gold: int = 150
var gold: int = 0
var base_health: int = 20

func _ready() -> void:
	gold = starting_gold

func add_gold(amount: int) -> void:
	gold += amount
	gold_changed.emit(gold)

func spend_gold(amount: int) -> bool:
	if gold >= amount:
		gold -= amount
		gold_changed.emit(gold)
		return true
	return false
	
func take_damage(amount: int) -> void:
	base_health = max(0, base_health - amount)
	health_changed.emit(base_health)
	
	if base_health <= 0:
		game_over.emit()
		print("You failed.")
