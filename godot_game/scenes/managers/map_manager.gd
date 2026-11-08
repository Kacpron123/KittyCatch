extends Node
class_name MapManager

var grid_data: Array = []
var buildable_grid: Array = []
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

	buildable_grid = grid_data.duplicate(true)
	return grid_data

func generate_route_grid(route: Path2D) -> Array:
	var route_grid = _empty_grid()
	if route.curve == null:
		return route_grid
	var baked_points = route.curve.get_baked_points()
	if baked_points.is_empty():
		return route_grid

	var previous_cell: Vector2i
	for i in range(baked_points.size()):
		var current_cell = world_to_grid(route.to_global(baked_points[i]))
		if i == 0:
			_mark_route_cell(route_grid, current_cell)
		else:
			_mark_route_line(route_grid, previous_cell, current_cell)
		previous_cell = current_cell
	return route_grid

func grid_to_world(x: int, y: int) -> Vector2:
	var rect = buildable_layer.get_used_rect()
	var tile_coords = Vector2i(x + rect.position.x, y + rect.position.y)
	return buildable_layer.to_global(buildable_layer.map_to_local(tile_coords))

func world_to_grid(world_position: Vector2) -> Vector2i:
	var rect = buildable_layer.get_used_rect()
	var tile_coords = buildable_layer.local_to_map(buildable_layer.to_local(world_position))
	return tile_coords - rect.position

func is_cell_buildable(x: int, y: int) -> bool:
	if x < 0 or x >= map_width or y < 0 or y >= map_height:
		return false
	return grid_data[x][y] == 1

func mark_cell_occupied(x: int, y: int):
	if is_cell_buildable(x, y):
		grid_data[x][y] = 2

func _empty_grid() -> Array:
	var grid: Array = []
	for x in range(map_width):
		var column: Array[int] = []
		column.resize(map_height)
		column.fill(0)
		grid.append(column)
	return grid

func _mark_route_cell(route_grid: Array, cell: Vector2i) -> void:
	if cell.x >= 0 and cell.x < map_width and cell.y >= 0 and cell.y < map_height:
		route_grid[cell.x][cell.y] = 1

func _mark_route_line(route_grid: Array, start: Vector2i, finish: Vector2i) -> void:
	var x = start.x
	var y = start.y
	var dx = absi(finish.x - start.x)
	var dy = absi(finish.y - start.y)
	var step_x = 1 if start.x < finish.x else -1
	var step_y = 1 if start.y < finish.y else -1
	var error = dx - dy

	while true:
		_mark_route_cell(route_grid, Vector2i(x, y))
		if x == finish.x and y == finish.y:
			break
		var double_error = 2 * error
		if double_error > -dy:
			error -= dy
			x += step_x
		if double_error < dx:
			error += dx
			y += step_y
