extends Node
class_name MapManager

var grid_data: Array = []
var map_width: int = 0
var map_height: int = 0

var buildable_layer: TileMapLayer

func generate_grid(level_node: Node) -> Array:
	grid_data.clear()
	
	buildable_layer = level_node.get_node("BuildableMap")
	var rect = buildable_layer.get_used_rect()
	
	map_width = rect.size.x
	map_height = rect.size.y
	
	for x in range(map_width):
		var column = []
		for y in range(map_height):
			column.append(0)
		grid_data.append(column)
	
	for x in range(map_width):
		for y in range(map_height):
			var tile_coords = Vector2i(x + rect.position.x, y + rect.position.y)
			if buildable_layer.get_cell_source_id(tile_coords) != -1:
				grid_data[x][y] = 1
				
	return grid_data

func grid_to_world(x: int, y: int) -> Vector2:
	var rect = buildable_layer.get_used_rect()
	var tile_coords = Vector2i(x + rect.position.x, y + rect.position.y)
	return buildable_layer.map_to_local(tile_coords)

func is_cell_buildable(x: int, y: int) -> bool:
	if x < 0 or x >= map_width or y < 0 or y >= map_height:
		return false
	return grid_data[x][y] == 1

func mark_cell_occupied(x: int, y: int):
	if is_cell_buildable(x, y):
		grid_data[x][y] = 2
