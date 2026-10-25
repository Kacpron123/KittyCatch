extends Node2D

@export var speed: float = 400.0
@export var hit_distance: float = 12.0

var target: Node2D = null
var damage: int = 0

func setup(p_target: Node2D, p_damage: int) -> void:
	target = p_target
	damage = p_damage

func _process(delta: float) -> void:
	if not is_instance_valid(target):
		queue_free()
		return

	var direction = (target.global_position - global_position).normalized()
	
	rotation = direction.angle()
	
	global_position += direction * speed * delta

	if global_position.distance_to(target.global_position) <= hit_distance:
		target.take_damage(damage)
		queue_free()
