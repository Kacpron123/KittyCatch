extends Node

signal connected_to_ai
signal disconnected_from_ai
signal ai_build_command_received(tower_type: String, grid_x: int, grid_y: int)

var tcp := StreamPeerTCP.new()
var host := "127.0.0.1"
var port := 8080

var _buffer := ""

func _ready():
	connect_to_server()

func connect_to_server():
	print("Łączenie z AI na porcie ", port, "...")
	tcp.connect_to_host(host, port)

func _process(_delta):
	tcp.poll()
	var state = tcp.get_status()
	
	if state == StreamPeerTCP.STATUS_CONNECTED:
		var available_bytes = tcp.get_available_bytes()
		if available_bytes > 0:
			var data = tcp.get_utf8_string(available_bytes)
			_process_incoming_data(data)
			
	elif state == StreamPeerTCP.STATUS_ERROR or state == StreamPeerTCP.STATUS_NONE:
		pass

func _process_incoming_data(new_data: String):
	_buffer += new_data
	
	var messages = _buffer.split("\n")
	_buffer = messages[messages.size() - 1]
	
	for i in range(messages.size() - 1):
		var msg_str = messages[i].strip_edges()
		if msg_str.is_empty(): continue
		var parsed_data = JSON.parse_string(msg_str)
		
		if typeof(parsed_data) == TYPE_DICTIONARY:
			_handle_message(parsed_data)
		else:
			push_error("Błąd parsowania JSON od AI: ", msg_str)

func _handle_message(message: Dictionary):
	if message.has("action") and message["action"] == "build_tower":
		var tower_type = message.get("tower_type", "laser")
		var x = message.get("x", 0)
		var y = message.get("y", 0)
		ai_build_command_received.emit(tower_type, x, y)
	
	elif message.has("action") and message["action"] == "upgrade":
		print("AI Upgrade?") 

func send_json(data: Dictionary):
	if tcp.get_status() == StreamPeerTCP.STATUS_CONNECTED:
		var json_string = JSON.stringify(data)
		var packet = json_string + "\n"
		tcp.put_data(packet.to_utf8_buffer())

func send_game_start(map_grid: Array, initial_money: int):
	var msg = {
		"type": "init",
		"map_grid": map_grid,
		"money": initial_money
	}
	send_json(msg)

func send_unit_positions(units_data: Array):
	var msg = {
		"type": "update",
		"units": units_data
	}
	send_json(msg)
