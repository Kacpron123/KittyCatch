extends Node2D

@export var tower_scene: PackedScene
@export var tower_cost: int = 100

@onready var map_layer: TileMapLayer = $map/Map
@onready var road_layer: TileMapLayer = $map/Road
@onready var towers_container: Node2D = $towers

var occupied_cells: Dictionary = {}

func _ready() -> void:
	$WaveManager.start_next_wave()
	
func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and event.pressed:
		try_place_tower(get_global_mouse_position())

func try_place_tower(click_position: Vector2) -> void:
	var cell: Vector2i = map_layer.local_to_map(map_layer.to_local(click_position))

	if not can_place_at(cell):
		print("Nie można postawić wieży w tym miejscu!")
		return

	if not GameManager.spend_gold(tower_cost):
		print("Za mało złota!")
		return

	var cell_center: Vector2 = map_layer.to_global(map_layer.map_to_local(cell))

	var tower = tower_scene.instantiate()
	tower.global_position = cell_center
	towers_container.add_child(tower)

	occupied_cells[cell] = true

func can_place_at(cell: Vector2i) -> bool:
	if occupied_cells.has(cell):
		return false

	if road_layer.get_cell_source_id(cell) != -1:
		return false

	if map_layer.get_cell_source_id(cell) == -1:
		return false

	return true
