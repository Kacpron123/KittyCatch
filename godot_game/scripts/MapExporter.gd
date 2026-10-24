@tool
extends Node

@export var export_now: bool = false : set = start_export

@export_group("Map Nodes")
@export var grass_layer: TileMapLayer
@export var road_layer: TileMapLayer
@export var path_2d: Path2D

@export_group("Grid Settings")
@export var map_width: int = 20
@export var map_height: int = 15

func start_export(value: bool):
	if value and grass_layer and road_layer and path_2d:
		generate_and_save()
	export_now = false

func generate_and_save():
	var grid = []
	
	for y in range(map_height):
		var row = []
		for x in range(map_width):
			var coords = Vector2i(x, y)
			
			var is_road = road_layer.get_cell_source_id(coords) != -1
			var is_grass = grass_layer.get_cell_source_id(coords) != -1
			
			if is_road:
				row.append(0)
			elif is_grass:
				row.append(1)
			else:
				row.append(0)
				
		grid.append(row)

	var path_points = []
	var curve = path_2d.curve
	if curve:
		for i in range(curve.get_point_count()):
			var pixel_pos = curve.get_point_position(i)
			var grid_pos = grass_layer.local_to_map(pixel_pos)
			path_points.append([grid_pos.x, grid_pos.y])

	var json_str = "{\n\t\"grid\": [\n"
	for i in range(grid.size()):
		json_str += "\t\t" + str(grid[i])
		if i < grid.size() - 1:
			json_str += ","
		json_str += "\n"
		
	json_str += "\t],\n\t\"path\": [\n"
	for i in range(path_points.size()):
		json_str += "\t\t" + str(path_points[i])
		if i < path_points.size() - 1:
			json_str += ","
		json_str += "\n"
		
	json_str += "\t]\n}"
	
	var file = FileAccess.open("res://config/map_data.json", FileAccess.WRITE)
	if file:
		file.store_string(json_str)
		file.close()
		print("Export successful! Format is compact.")
	else:
		print("Save error!")
