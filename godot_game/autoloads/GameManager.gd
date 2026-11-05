extends Node

var selected_level_path: String = "res://scenes/levels/level1.tscn"
var tile_size: int = 64

signal health_changed(new_health: int)
signal money_changed(new_money: int)
signal game_over()

# Stan bieżącej rozgrywki
var base_health: int = 20
var money: int = 500

func start_new_game(starting_health: int = 20, starting_money: int = 500):
	base_health = starting_health
	money = starting_money
	health_changed.emit(base_health)
	money_changed.emit(money)

func take_damage(amount: int):
	base_health -= amount
	health_changed.emit(base_health)
	
	if base_health <= 0:
		base_health = 0
		trigger_game_over()

func trigger_game_over():
	print("Koniec gry! Baza zniszczona.")
	game_over.emit()

func add_gold(amount: int):
	money += amount
	money_changed.emit(money)

func spend_gold(amount: int) -> bool:
	if money >= amount:
		money -= amount
		money_changed.emit(money)
		return true
	return false
