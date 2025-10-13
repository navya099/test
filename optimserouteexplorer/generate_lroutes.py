from optimserouteexplorer.curveadjuster import CurveAdjuster
from optimserouteexplorer.evaluate import Evaluate
from optimserouteexplorer.linestringprocessor import LineStringProcessor
from optimserouteexplorer.profilecreator import ProfileCreator
from optimserouteexplorer.randomlinestringcreator import RandomLineStringCreator
from optimserouteexplorer.util import calc_pl2xy, adjust_radius_by_angle, calc_pl2xy_array, sample_elevations, haversine
from shapely.geometry import Point
from optimserouteexplorer.alignment import Alignment
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm
from asyncio import as_completed

class GenerateRoutes:
    def __init__(self):
        self.alignments = None

    def generate_candidate(self, idx, start, end, chain):


        start_tm = calc_pl2xy((start[1], start[0]))
        end_tm = calc_pl2xy((end[1], end[0]))

        random_linestring_creator = RandomLineStringCreator()

        random_linestring_creator.generate_random_linestring(Point(start_tm), Point(end_tm))

        linestring = random_linestring_creator.linestring
        linestringprocessor = LineStringProcessor(linestring)
        linestringprocessor.process_linestring()
        linestring = linestringprocessor.linestring

        angles = linestringprocessor.angles
        radius_list = [adjust_radius_by_angle(angle, 3100, 20000) for angle in angles]

        curveadjustor = CurveAdjuster(linestring, angles, radius_list)
        curveadjustor.main_loop()
        curvelist = curveadjustor.segments

        start_points = [curve.bc_coord for curve in curvelist]
        end_points = [curve.ec_coord for curve in curvelist]
        center_points = [curve.center_coord for curve in curvelist]
        direction_list = [curve.direction for curve in curvelist]

        linestringprocessor.create_joined_line_and_arc_linestirng(
            start_points=start_points,
            end_points=end_points,
            center_points=center_points,
            direction_list=direction_list
        )
        linestringprocessor.resample_linestring(chain)
        coords = list(linestringprocessor.linestring.coords)
        coords = calc_pl2xy_array(coords)
        coords = [(y,x) for x,y in coords]

        ground_elevs = sample_elevations(coords)

        distances = [0]
        for i in range(1, len(coords)):
            distances.append(distances[-1] + haversine(coords[i - 1], coords[i]) / 1000)  # km

        gl = [(sta * 1000, ele) for sta, ele in zip(distances , ground_elevs)]
        min_distance = 1000
        max_vip = int(gl[-1][0] / min_distance)
        profilecreator = ProfileCreator(gl)
        profilecreator.generate_longitudinal(
            num_points=max_vip,
            min_distance=min_distance,
            chain=chain
        )
        design_elevs = profilecreator.els
        profile = profilecreator.profile
        evaluator = Evaluate()
        cost, bridges, tunnels , slopes = evaluator.evaluate_longitudinal(coords, design_elevs, ground_elevs)


        return Alignment(
            coords=coords,
            elevations=design_elevs,
            grounds=ground_elevs,
            bridges=bridges,
            tunnels=tunnels,
            cost=cost,
            fls=profile,
            grades=slopes,
            radius=radius_list
        )

    def generate_and_rank_parallel(self, start, end, n_candidates=30, chain=40):
        alignments = []


        with ProcessPoolExecutor() as executor:
            futures = {executor.submit(self.generate_candidate, i, start, end, chain): i for i in range(n_candidates)}


            for future in tqdm(as_completed(futures), total=n_candidates, desc="Generating candidates"):
                try:
                    alignments.append(future.result())
                except Exception as e:
                    idx = futures[future]
                    print(f"Candidate {idx} failed: {e}")

        # 비용 기준 정렬
        alignments.sort(key=lambda x: x.cost)
        return alignments

    def generate_and_rank(self, start, end, n_candidates=30, chain=40):
        alignments = []
        for i in range(n_candidates):
            alignments.append(self.generate_candidate( i, start, end, chain))
        # 비용 기준 정렬
        alignments.sort(key=lambda x: x.cost)
        return alignments