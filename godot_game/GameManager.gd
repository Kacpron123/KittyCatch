extends Node

signal gold_changed(new_amount: int)

@export var starting_gold: int = 550
var gold: int = 0

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
