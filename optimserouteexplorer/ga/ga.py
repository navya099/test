from geometry.alignment import Alignment

class GeneticAlgorithm:
    def __init__(self, start, end, n_candidates=30, n_generations=20, chain=40,
                 elite_ratio=0.2, mutation_rate=0.1):
        self.start = start
        self.end = end
        self.n_candidates = n_candidates
        self.n_generations = n_generations
        self.chain = chain
        self.elite_ratio = elite_ratio
        self.mutation_rate = mutation_rate

        self.population: list[Alignment] = []

    def initialize_population(self):
        self.population = [generate_candidate(i, self.start, self.end, self.chain)
                           for i in range(self.n_candidates)]

    def selection(self):
        # 상위 절반에서 부모 선택
        sorted_pop = sorted(self.population, key=lambda x: x.cost)
        n_elite = max(2, int(self.elite_ratio * len(sorted_pop)))
        elites = sorted_pop[:n_elite]
        parents = random.choices(sorted_pop[:len(sorted_pop) // 2], k=len(sorted_pop))
        return elites, parents

    def crossover_and_mutate(self, parents: list[Alignment]):
        children = []
        for i in range(0, len(parents), 2):
            if i + 1 >= len(parents):
                break
            p1, p2 = parents[i], parents[i + 1]
            child = crossover_routes(p1, p2)
            mutate_route(child, self.mutation_rate)
            children.append(child)
        return children

    def evolve(self):
        self.initialize_population()
        for gen in range(self.n_generations):
            print(f"=== Generation {gen + 1}/{self.n_generations} ===")
            # 병렬 평가
            self.population = evaluate_population_parallel(self.population)

            elites, parents = self.selection()
            children = self.crossover_and_mutate(parents)
            self.population = elites + children
            self.population = self.population[:self.n_candidates]  # 인구수 유지

        # 최종 정렬
        self.population.sort(key=lambda x: x.cost)
        return self.population
