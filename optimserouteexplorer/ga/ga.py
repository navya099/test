import random
from copy import deepcopy
from core.generate_routes import GenerateRoutes
from core.evaluate import Evaluator
from core.plan_creator import PlanCreator


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

        self.population = []  # GA 후보: ip_list + meta + fitness/cost

    # -------------------------------
    # 1️⃣ 초기 후보 생성 (IP만)
    # -------------------------------
    def initialize_population(self):
        gr = GenerateRoutes()
        self.population = []

        for _ in range(self.n_candidates):
            plan ,ia = gr.generate_ip_linestring(self.start, self.end)
            self.population.append(
                {'plan': plan,
                 'ia': ia,
                 "fitness": None,
                 "cost": None,
                 "score": None
                 }
            )

    # -------------------------------
    # 2️⃣ 후보 평가 (필요 시만 계산)
    # -------------------------------
    def evaluate_candidate(self, candidate):
        gr = GenerateRoutes()
        evl = Evaluator()
        ac = PlanCreator(self.start, self.end, self.chain)
        radius_list = ac.calculate_radius_list(candidate['ia'])
        # IP 좌표 → 전체 평면(LineString + 곡선) 재구성
        plan_full = ac.reconstruct_full_plan(candidate['ip_list'], candidate['ia'], radius_list, self.chain)

        # 종단(profile) 생성
        profile = gr.generate_profile_candidate(
            plan_full['wgs_coords'], self.chain, plan_full['station_list']
        )

        # 비용/점수/적합도 평가
        result = evl.evaluate(plan_full, profile, self.chain)

        candidate.update({
            "cost": result['total_cost'],
            "score": result['total_score'],
            "fitness": result['total_fitness']
        })

    # -------------------------------
    # 3️⃣ 선택 (엘리트 + 부모)
    # -------------------------------
    def selection(self):
        sorted_pop = sorted(self.population, key=lambda x: x['fitness'], reverse=True)
        n_elite = max(2, int(self.elite_ratio * len(sorted_pop)))
        elites = deepcopy(sorted_pop[:n_elite])

        parents = random.choices(sorted_pop[:len(sorted_pop)//2], k=len(sorted_pop))
        return elites, parents

    # -------------------------------
    # 4️⃣ 교배 + 돌연변이
    # -------------------------------
    def crossover_and_mutate(self, parents):
        children = []
        for i in range(0, len(parents), 2):
            if i+1 >= len(parents):
                break
            p1, p2 = parents[i], parents[i+1]

            # IP 좌표 교배
            child_ip = self.crossover_ip_list(p1['ip_list'], p2['ip_list'])
            # IP 좌표 돌연변이
            child_ip = self.mutate_ip_list(child_ip)

            child = {
                "ip_list": child_ip,
                "meta": deepcopy(p1['meta']),  # 메타는 부모1 복사
                "fitness": None,
                "cost": None,
                "score": None
            }
            children.append(child)
        return children

    # -------------------------------
    # 5️⃣ GA 연산용 crossover/mutation (단순 샘플)
    # -------------------------------
    def crossover_ip_list(self, ip1, ip2):
        # 단순 절반 교차
        n = min(len(ip1), len(ip2))
        cut = n // 2
        return ip1[:cut] + ip2[cut:]

    def mutate_ip_list(self, ip_list):
        mutated = []
        for pt in ip_list:
            # 간단한 위치 변화 (예: ±10m)
            x = pt.x + random.uniform(-10, 10)
            y = pt.y + random.uniform(-10, 10)
            mutated.append(pt.__class__(x, y))
        return mutated

    # -------------------------------
    # 6️⃣ 전체 GA 루프
    # -------------------------------
    def evolve(self):
        self.initialize_population()

        for gen in range(self.n_generations):
            print(f"=== Generation {gen+1}/{self.n_generations} ===")

            # 후보 평가 (fitness 없는 경우만 계산)
            for cand in self.population:
                if cand['fitness'] is None:
                    self.evaluate_candidate(cand)

            # 선택
            elites, parents = self.selection()

            # 교배 + 돌연변이
            children = self.crossover_and_mutate(parents)

            # 다음 세대
            self.population = elites + children
            self.population = self.population[:self.n_candidates]

        # 최종 정렬: fitness 기준 내림차순
        self.population.sort(key=lambda x: x['fitness'], reverse=True)
        return self.population
