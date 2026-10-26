from src.genetic_ai import GeneticAgent
from src.simulator import Simulator

genetic_agent = GeneticAgent()
sim = Simulator(config_data, map_data)

state = sim.to_dict()
action = genetic_agent.predict(state)

# Przykładowa akcja:
# {"action": "spawn", "unit_type": "tank"}

# Wykonaj akcję w symulatorze.
# Następnie zaktualizuj stan i powtórz.
