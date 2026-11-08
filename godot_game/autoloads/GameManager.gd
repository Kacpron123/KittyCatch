extends Node

var selected_level_path: String = "res://scenes/levels/level1.tscn"
var tile_size: int = 64

signal health_changed(current_health: int, max_health: int)
signal energy_changed(current_energy: int, max_energy: int)
signal tower_money_changed(new_money: int)
signal game_over()

var max_health: int = 1000
var base_health: int = 1000

var max_energy: int = 40
var energy: int = 40
var tower_money: int = 100

func start_new_game(starting_health: int = 1000, starting_energy: int = 40, starting_money: int = 100):
	max_health = starting_health
	base_health = starting_health
	energy = starting_energy
	tower_money = starting_money
	
	health_changed.emit(base_health, max_health)
	energy_changed.emit(energy, max_energy)
	tower_money_changed.emit(tower_money)

func take_damage(amount: int):
	base_health -= amount
	if base_health <= 0:
		base_health = 0
		trigger_game_over()
		
	health_changed.emit(base_health, max_health)

func trigger_game_over():
	print("Koniec gry! Baza zniszczona.")
	game_over.emit()

func add_gold(amount: int):
	tower_money += amount
	tower_money_changed.emit(tower_money)

func spend_gold(amount: int) -> bool:
	if tower_money >= amount:
		tower_money -= amount
		tower_money_changed.emit(tower_money)
		return true
	return false

func add_energy(amount: int):
	energy = min(energy + amount, max_energy) 
	energy_changed.emit(energy, max_energy)

func spend_energy(amount: int) -> bool:
	if energy >= amount:
		energy -= amount
		energy_changed.emit(energy, max_energy)
		return true
	return false
