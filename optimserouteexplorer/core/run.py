from ga.ga import GeneticAlgorithm
from out.out_ga import format_top10


def run_process(start, end, n_candidates, n_generations):
    ga = GeneticAlgorithm(start, end, n_candidates, n_generations)
    population = ga.evolve()
    return population



