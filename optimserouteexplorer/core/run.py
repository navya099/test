from ga.ga import GeneticAlgorithm
from out.out_ga import format_top10


def run_process(start, end, n_candidates, n_generations, top_n):
    ga = GeneticAlgorithm(start, end, n_candidates, n_generations)
    population = ga.evolve()
    top10 = format_top10(population, top_n)
    return top10



