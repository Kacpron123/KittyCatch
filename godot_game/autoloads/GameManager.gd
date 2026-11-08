extends Node

var selected_level_path: String = "res://scenes/levels/level1.tscn"
var tile_size: int = 64

signal health_changed(current_health: int, max_health: int)
signal energy_changed(current_energy: int, max_energy: int)
signal ai_money_changed(new_money: int)
signal game_over()

var max_health: int = 1000
var base_health: int = 1000

var max_energy: int = 40
var energy: int = 40
var energy_regen_per_second: float = 1.0
var kill_energy_refund_fraction: float = 0.6
var ai_money: int = 150
var enemy_speed_multiplier: float = 1.0
var enemy_speed_bonus_per_base_hit: float = 0.005
var max_enemy_speed_bonus: float = 0.1

var _energy_regen_accumulator: float = 0.0

func _process(delta: float) -> void:
	if energy >= max_energy or energy_regen_per_second <= 0.0:
		_energy_regen_accumulator = 0.0
		return

	_energy_regen_accumulator += energy_regen_per_second * delta
	while _energy_regen_accumulator >= 1.0 and energy < max_energy:
		_energy_regen_accumulator -= 1.0
		add_energy(1)

func start_new_game(
	starting_health: int = 1000,
	starting_energy: int = 40,
	starting_ai_money: int = 150,
	energy_capacity: int = 100,
	energy_regen: float = 1.0,
	energy_refund_fraction: float = 0.6,
	speed_bonus_per_base_hit: float = 0.005,
	max_speed_bonus: float = 0.1
) -> void:
	max_health = starting_health
	base_health = starting_health
	max_energy = maxi(0, energy_capacity)
	energy = clampi(starting_energy, 0, max_energy)
	energy_regen_per_second = maxf(0.0, energy_regen)
	kill_energy_refund_fraction = clampf(energy_refund_fraction, 0.0, 1.0)
	_energy_regen_accumulator = 0.0
	ai_money = maxi(0, starting_ai_money)
	enemy_speed_bonus_per_base_hit = maxf(0.0, speed_bonus_per_base_hit)
	max_enemy_speed_bonus = maxf(0.0, max_speed_bonus)
	enemy_speed_multiplier = 1.0
	
	health_changed.emit(base_health, max_health)
	energy_changed.emit(energy, max_energy)
	ai_money_changed.emit(ai_money)

func take_damage(amount: int) -> void:
	if amount <= 0 or base_health <= 0:
		return

	var current_speed_bonus = enemy_speed_multiplier - 1.0
	if current_speed_bonus < max_enemy_speed_bonus:
		enemy_speed_multiplier = 1.0 + minf(
			current_speed_bonus + enemy_speed_bonus_per_base_hit,
			max_enemy_speed_bonus
		)

	base_health = maxi(0, base_health - amount)
	if base_health == 0:
		trigger_game_over()
		
	health_changed.emit(base_health, max_health)

func trigger_game_over() -> void:
	print("Koniec gry! Baza zniszczona.")
	game_over.emit()

func add_ai_money(amount: int) -> void:
	if amount <= 0:
		return
	ai_money += amount
	ai_money_changed.emit(ai_money)

func spend_ai_money(amount: int) -> bool:
	if amount < 0 or ai_money < amount:
		return false
	ai_money -= amount
	ai_money_changed.emit(ai_money)
	return true

func add_energy(amount: int) -> void:
	if amount <= 0:
		return
	var previous_energy = energy
	energy = mini(energy + amount, max_energy)
	if energy != previous_energy:
		energy_changed.emit(energy, max_energy)

func spend_energy(amount: int) -> bool:
	if amount < 0 or energy < amount:
		return false
	energy -= amount
	energy_changed.emit(energy, max_energy)
	return true
