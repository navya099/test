from coord.coord_sampler import CoordinateProcessor
import logging

from mesh.mesh_modifier import MeshModifier
from out.output_manger import OutputExporter
from plot.plot import MeshPlotter
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
        terrain_mesh = terrain_builder.build()
        slope_manager = SlopeManager(self.dem_processor, terrain_mesh)

        # ── 2. 모든 트랙의 사면을 누적 ───────────────────────────
        all_slope_lefts = []
        all_slope_rights = []
        track_meshes = []  # 시각화/저장용

        # 메인 트랙
        seg_coords = CoordinateProcessor.filter_coords_by_segment(self.read_coords, seg)
        if len(seg_coords) >= 2:
            track_mesh, slope_lefts, slope_rights = self._build_slopes_for_track(
                idx, seg, seg_coords, slope_manager, track_no=0
            )
            if track_mesh:
                track_meshes.append(track_mesh)
                all_slope_lefts.extend(slope_lefts)
                all_slope_rights.extend(slope_rights)

        # 추가 트랙
        if self.tracks:
            for track_no, coords in self.tracks.items():
                seg_coords_extra = CoordinateProcessor.filter_coords_by_segment(coords, seg)
                if len(seg_coords_extra) >= 2:
                    track_mesh_extra, slope_lefts_extra, slope_rights_extra = self._build_slopes_for_track(
                        idx, seg, seg_coords_extra, slope_manager, track_no=track_no
                    )
                    if track_mesh_extra:
                        track_meshes.append(track_mesh_extra)
                        all_slope_lefts.extend(slope_lefts_extra)
                        all_slope_rights.extend(slope_rights_extra)

        if not all_slope_lefts:
            logging.warning(f"Segment {idx}: 생성된 사면 없음 → 스킵")
            return

        # ── 3. 지형 클리핑 1회 (모든 트랙 사면 반영) ─────────────
        logging.info(f"Segment {idx} 지형 클리핑 시작 (사면 총 {len(all_slope_lefts)}개)")
        terrain_assembler = TerrainAssembler(self.dem_processor, slope_manager)
        clipped_terrain, fixed_slope_lefts, fixed_slope_rights = terrain_assembler.build(
            idx, all_slope_lefts, all_slope_rights, terrain_mesh
        )

        # ── 4. 평행이동 ───────────────────────────────────────────
        clipped_terrain = MeshModifier(clipped_terrain).translate(self.xyz_list[idx - 1])
        track_meshes = [MeshModifier(tm).translate(self.xyz_list[idx - 1]) for tm in track_meshes]
        fixed_slope_lefts = [MeshModifier(sl).translate(self.xyz_list[idx - 1]) for sl in fixed_slope_lefts]
        fixed_slope_rights = [MeshModifier(sr).translate(self.xyz_list[idx - 1]) for sr in fixed_slope_rights]

        # ── 5. 저장 ───────────────────────────────────────────────
        # 메인 트랙 기준으로 저장 (track_meshes[0])
        main_track = track_meshes[0] if track_meshes else None
        OutputExporter.save_obj_with_groups(
            f"c:/temp/obj/segment_{idx}.obj",
            clipped_terrain.points, clipped_terrain.cells[0].data,
            main_track.points if main_track else None,
            main_track.cells[0].data if main_track else None,
            fixed_slope_lefts,
            fixed_slope_rights
        )
        logging.info(f"병합된 지표면 저장 완료: segment_{idx}")

        # ── 6. 시각화 ─────────────────────────────────────────────
        if is_visible:
            plot_items = [
                (clipped_terrain.points, clipped_terrain.cells[0].data, "orange", "Clipped Terrain")
            ]
            for i, tm in enumerate(track_meshes):
                plot_items.append((tm.points, tm.cells[0].data, "blue", f"Track {i}"))
            for i, sl in enumerate(fixed_slope_lefts, start=1):
                plot_items.append((sl.points, sl.cells[0].data, "green", f"Slope Left {i}"))
            for i, sr in enumerate(fixed_slope_rights, start=1):
                plot_items.append((sr.points, sr.cells[0].data, "red", f"Slope Right {i}"))
            MeshPlotter.plot_multiple_meshes(plot_items)

    def _build_slopes_for_track(self, idx, seg, seg_coords, slope_manager, track_no=0):
        """
        단일 트랙의 토공 구간별 사면을 생성하고 반환.
        지형 생성/클리핑은 하지 않음 (process_segment에서 통합 처리).
        반환: (track_mesh, slope_lefts, slope_rights)
        """
        label = f"Track {track_no}" if track_no else "Main Track"
        logging.info(f"Segment {idx} [{label}] 사면 생성 시작")

        # 트랙 빌더
        track_manager = TrackProcessor(seg_coords)
        track_mesh, track_edges = track_manager.build_track()

        # 측점 및 토공 구간 분리
        stations = get_stations(self.read_coords, seg_coords) if label == "Main Track" else [pt[-1] for pt in seg_coords]
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