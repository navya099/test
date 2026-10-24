import logging
logging.basicConfig(level=logging.DEBUG)

from ga.ga import GeneticAlgorithm
ga = GeneticAlgorithm((37.5665, 126.9780), (37.4870, 127.1000), n_candidates=3, n_generations=1)
pop = ga.evolve(seed=1)

for c in pop:
    print("fitness:", c["fitness"])
    print("constraints_ok:", c.get("constraints_ok"))
    print("radius_list:", c.get("radius_list"))
    print("slopes:", c.get("profile", {}).get("slopes"))
    print("---")