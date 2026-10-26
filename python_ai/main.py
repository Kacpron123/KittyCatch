import os
from src.data import load_game_data
from src.simulator import Simulator
from src.visualization import render_state
from src.visualization import write_state_to_file

def main():
    os.makedirs("frames", exist_ok=True)

    config, map_data = load_game_data()
    print("Dane wczytane poprawnie.")

    sim = Simulator(config, map_data)

    sim.build_tower(10, 6, "basic")
    sim.spawn_enemy("scout")

    for i in range(50):
        sim.step(dt=0.5)

        frame_path = f"frames/frame_{i:03d}.png"
        render_state(sim, frame_path)
        write_state_to_file(sim, f"frames/state_{i:03d}.json")

        if not sim.enemies:
            print(f"Tick {i}: Koniec wrogów. Złoto: {sim.gold}, HP Bazy: {sim.base_hp}")
            break

    print("Symulacja zakończona. Klatki zapisano w folderze 'frames/'.")

if __name__ == "__main__":
    main()
