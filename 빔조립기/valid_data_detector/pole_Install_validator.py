from library import LibraryManager
from valid_data_detector.relust import ValidationResult
from vector3 import Vector3


class PoleInstallValidator:
    @staticmethod
    def validate(data: dict, lib_manager: LibraryManager) -> ValidationResult:
        result = ValidationResult()

        PoleInstallValidator._validate_poles(data['poles'], result)
        PoleInstallValidator._validate_beams(data['beams'], result)
        PoleInstallValidator._validate_rails(data['rails'], lib_manager, result)

        return result

    @staticmethod
    def _validate_poles(poles: list, result: ValidationResult):
        # beam_type
        for pole in poles:
            #전주타입검사
            if pole.get("type") not in ["강관주", "H형강주", "조립철주"]:
                result.errors.append(
                    f"알 수 없는 전주 타입: {pole.get('type')}"
                )
            #전주길이검사
            if not isinstance(pole.get("length"), float):
                result.errors.append(
                    f"전주 길이는 숫자여야 합니다.: {pole.get('length')}"
                )
            #전주 규격검사
            if pole.get('width') not in ["P10",'P12','P14','P16','P18','P20']:
                result.errors.append(
                    f"유효하지 않은 전주 규격입니다.: {pole.get('width')}"
                )
            #오프셋검사
            if not isinstance(pole.get("xoffset"), float):
                result.errors.append(
                    f"건식게이지는 숫자여야 합니다.: {pole.get('length')}"
                )

    @staticmethod
    def _validate_beams(beams: list, result: ValidationResult):
        # beam_type
        for beam in beams:
            # 빔타입검사
            if beam.get("type") not in ["트러스빔", "트러스라멘빔", "강관빔", 'V트러스빔']:
                result.errors.append(
                    f"알 수 없는 빔 타입: {beam.get('type')}"
                )
            #시작 전주 끝 전주 검사
            if not isinstance(beam.get("start_pole"), int) or not isinstance(beam.get("end_pole"), int):
                result.errors.append(
                    f"시작과 끝 전주는 숫자여야 합니다.: {beam.get('start_pole'), {beam.get('end_pole')}}"
                )

    @staticmethod
    def _validate_rails(rails, lib_manager, result: ValidationResult):
        seen_indices = set()

        for i, rail in enumerate(rails):
            name = rail.get("name", f"#{i}")
            idx = rail.get("index")
            #인덱스 유효성 검사
            if not isinstance(idx, int):
                result.errors.append(f"[선로 {name}] index는 정수여야 합니다")
                continue

            # index 중복검사
            if idx in seen_indices:
                result.errors.append(f"[선로 {name}] index 중복: {idx}")
            seen_indices.add(idx)

            # coord 필드 누락검사
            coord = rail.get("coord")
            if coord is None:
                result.errors.append(f"[선로 {name}] coord 누락")
                continue
            #타입체크
            if not isinstance(coord, Vector3):
                result.errors.append(f"[선로 {name}] coord 형식 오류")
                continue

            for k in ("x", "y", "z"):
                v = getattr(coord, k, None)
                if not isinstance(v, (int, float)):
                    result.errors.append(
                        f"[선로 {name}] coord.{k} 는 숫자여야 합니다"
                    )

            PoleInstallValidator._validate_brackets(rail, lib_manager, result)

    @staticmethod
    def _validate_brackets(rail, lib, result: ValidationResult):
        rname = rail.get("name", "?")

        for b in rail.get("brackets", []):
            btype = b.get("type")
            rail_type = b.get("rail_type")

            # ❌ rail_type 자체가 이상 → ERROR
            if rail_type not in ["일반철도", "도시철도", "준고속철도", "고속철도"]:
                result.errors.append(
                    f"[선로 {rname}] 잘못된 rail_type: {rail_type}"
                )
                continue

            group = lib.define_group(rail_type)
            bracket_list = lib.list_files_in_category('브래킷', group)

            # ❌ 없는 브래킷 → WARNING (무시 가능)
            if not btype in bracket_list:
                result.warnings.append(
                    f"[선로 {rname}] 브래킷 없음: {btype} (무시됨)"
                )


            # rotation 범위
            rot = b.get("rotation", 0)
            if not isinstance(rot, (int, float)):
                result.errors.append(
                    f"[선로 {rname}] rotation 값 오류"
                )
            elif not (0 <= rot <= 360):
                result.warnings.append(
                    f"[선로 {rname}] rotation {rot} → 0~360 범위 초과 (보정 예정)"
                )
