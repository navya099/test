from rich.progress import track

from coord.coord_sampler import CoordinateProcessor
import logging

from mesh.mesh_modifier import MeshModifier
from out.output_manger import OutputExporter
from plot.plot import MeshPlotter
from slope.slope_assembler import SlopeAssembler
from slope.slope_manager import SlopeManager
from terrain.terrain_assembler import TerrainAssembler
from track.processor import TrackProcessor
from terrain.terrain_builder import TerrainBuilder
from util import get_stations, get_earthwork_sections


class SegmentProcessor:
    def __init__(self, dem_processor, xyz_list, structure_list, tracks, read_coords):
        self.dem_processor = dem_processor
        self.xyz_list = xyz_list
        self.structure_list = structure_list
        self.tracks = tracks
        self.read_coords = read_coords

    def process_segment(self, idx, seg, is_visible=False):
        """세그먼트 처리 메서드 - 1개 지형에 모든 트랙 사면 반영"""

        # ── 1. 지형 1회 생성 ──────────────────────────────────────
        terrain_builder = TerrainBuilder(self.dem_processor, seg)
        terrain_mesh = terrain_builder.build(idx)
        slope_manager = SlopeManager(self.dem_processor, terrain_mesh)

        # ── 2. 모든 트랙의 사면을 누적 ───────────────────────────
        all_slope_lefts = []
        all_slope_rights = []
        track_meshes = []  # 시각화/저장용

        #트랙별 순회
        track_names = []
        if self.tracks:
            for alignment in self.tracks:
                track_no = next((rail.railindex for rail in alignment.raildata if rail), None) #선로번호 가져오기
                track_name = alignment.name #선로명
                track_rails = [(rail.station, rail.coord.x,rail.coord.y, rail.coord.z) for rail in alignment.raildata] #vector3객체를 x,y,z튜플로 변환
                seg_coords = CoordinateProcessor.filter_coords_by_segment(track_rails, seg) #전체 트랙에서 구간 분리

                # (x, y, z)만 추출
                track_coords = [(x, y, z) for (station, x, y, z) in seg_coords]
                track_stations = [station for (station, x, y, z) in seg_coords]

                logging.info(f'트랙: {track_name}, 선로번호: {track_no} 번 작업 시작')

                if len(seg_coords) >= 2:
                    track_mesh, slope_lefts, slope_rights = self._build_slopes_for_track(
                        idx, track_name, track_stations, track_coords, slope_manager)
                    if track_mesh:
                        track_meshes.append(track_mesh)
                        all_slope_lefts.extend(slope_lefts)
                        all_slope_rights.extend(slope_rights)
                track_names.append(track_name)
        if not all_slope_lefts:
            logging.warning(f"Segment {idx}: 생성된 사면 없음 → 스킵")
            return

        # ── 3. 지형 클리핑 1회 (모든 트랙 사면 반영) ─────────────
        logging.info(f"Segment {idx} 지형 클리핑 시작 (사면 총 {len(all_slope_lefts)}개)")
        terrain_assembler = TerrainAssembler(self.dem_processor, slope_manager)
        clipped_terrain, fixed_slope_lefts, fixed_slope_rights = terrain_assembler.build(
            idx, all_slope_lefts, all_slope_rights, terrain_mesh
        )

        #TODO 사면끼리 클리핑 구현
        """#    ── 3-1. 사면끼리 클리핑 ─────────────
        logging.info(f"Segment {idx} 지형 클리핑 시작 (사면 총 {len(all_slope_lefts)}개)")
        slope_assembler = SlopeAssembler(fixed_slope_lefts, fixed_slope_rights)
        fixed_slope_lefts, fixed_slope_rights = slope_assembler.clip_slopes()"""

        # ── 4. 평행이동 ───────────────────────────────────────────
        logging.info(f"Segment {idx} 평행이동")
        clipped_terrain = MeshModifier(clipped_terrain).translate(self.xyz_list[idx - 1])
        track_meshes = [MeshModifier(tm).translate(self.xyz_list[idx - 1]) for tm in track_meshes]
        fixed_slope_lefts = [MeshModifier(sl).translate(self.xyz_list[idx - 1]) for sl in fixed_slope_lefts]
        fixed_slope_rights = [MeshModifier(sr).translate(self.xyz_list[idx - 1]) for sr in fixed_slope_rights]

        # ── 5. 저장 ───────────────────────────────────────────────
        logging.info(f"Segment {idx} 저장중...")
        save_items = [
            (clipped_terrain.points, clipped_terrain.cells[0].data, "orange", "Clipped Terrain")
        ]
        for tm, name in zip(track_meshes, track_names):
            save_items.append((tm.points, tm.cells[0].data, "blue", f"Track {name}"))
        for i, sl in enumerate(fixed_slope_lefts, start=1):
            save_items.append((sl.points, sl.cells[0].data, "green", f"Slope Left {i}"))
        for i, sr in enumerate(fixed_slope_rights, start=1):
            save_items.append((sr.points, sr.cells[0].data, "red", f"Slope Right {i}"))

        OutputExporter.save_obj_with_groups(f"c:/temp/obj/segment_{idx}.obj", save_items)
        logging.info(f"병합된 지표면 저장 완료: segment_{idx}")

        # ── 6. 시각화 ─────────────────────────────────────────────
        if is_visible:
            logging.info(f"Segment {idx} 시각화 중...")
            MeshPlotter.plot_multiple_meshes(save_items)

        logging.info(f"Segment {idx} 모든 작업 완료!")

    def _build_slopes_for_track(self, idx, label, stations, seg_coords, slope_manager):
        """
        단일 트랙의 토공 구간별 사면을 생성하고 반환.
        지형 생성/클리핑은 하지 않음 (process_segment에서 통합 처리).
        반환: (track_mesh, slope_lefts, slope_rights)
        """

        logging.info(f"Segment {idx} [{label}] 사면 생성 시작")

        # 트랙 빌더
        track_manager = TrackProcessor(seg_coords)
        track_mesh, track_edges = track_manager.build_track()

        earth_list = get_earthwork_sections(seg_coords, stations, self.structure_list)

        seg_start_sta = stations[0]
        seg_end_sta = stations[-1]
        logging.info(f"Segment {idx} [{label}] 범위: {seg_start_sta} ~ {seg_end_sta}, 토공 구간: {len(earth_list)}개")

        # 토공 구간별 사면 생성
        slope_lefts = []
        slope_rights = []
        for corridor_idx, corridor in enumerate(earth_list, start=1):
            logging.info(f"Segment {idx} [{label}] Corridor {corridor_idx} 사면 생성")
            earth_left_side = [track_edges[0][i] for i in corridor["indices"]]
            earth_right_side = [track_edges[1][i] for i in corridor["indices"]]

            slope_left, slope_right = slope_manager.build_slopes(
                (earth_left_side, earth_right_side), slope_ratio=1.5
            )
            slope_lefts.append(slope_left)
            slope_rights.append(slope_right)

        return track_mesh, slope_lefts, slope_rights