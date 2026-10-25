extends PathFollow2D

@export var speed: float = 150.0
@export var health: int = 100

func _process(delta: float) -> void:
	progress += speed * delta
	if progress_ratio >= 1.0:
		reach_end()

func take_damage(amount: int) -> void:
	health -= amount
	if health <= 0:
		die()

func reach_end() -> void:
	queue_free()

func die() -> void:
	queue_free()
