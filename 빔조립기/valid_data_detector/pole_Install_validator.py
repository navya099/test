from library import LibraryManager
from valid_data_detector.relust import ValidationResult
from vector3 import Vector3


class PoleInstallValidator:
    @staticmethod
    def validate(data: dict, lib_manager: LibraryManager) -> ValidationResult:
        result = ValidationResult()

        PoleInstallValidator._validate_header(data, result)
        PoleInstallValidator._validate_rails(data, lib_manager, result)

        return result

    @staticmethod
    def _validate_header(data, result: ValidationResult):
        # beam_type
        if data.get("beam_type") not in ["강관빔", "트러스빔", "트러스라멘빔", 'V트러스빔']:
            result.errors.append(
                f"알 수 없는 빔 타입: {data.get('beam_type')}"
            )

        # pole_type
        if data.get("pole_type") not in ["강관주", "H형강주", "조립철주"]:
            result.errors.append(
                f"알 수 없는 전주 타입: {data.get('pole_type')}"
            )

        # rail_count
        if data.get("rail_count") != len(data.get("rails", [])):
            result.warnings.append(
                "rail_count와 실제 rails 개수가 다릅니다. rails 기준으로 처리합니다."
            )

    @staticmethod
    def _validate_rails(data, lib_manager, result: ValidationResult):
        seen_indices = set()

        for i, rail in enumerate(data.get("rails", [])):
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
