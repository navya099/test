# core/world.py
import logging
from core.system.system import System

logger = logging.getLogger(__name__)


class ValidatedStore(dict):
    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError:
            raise KeyError(f"'{key}'가 없습니다. 등록된 키: {sorted(self.keys())}") from None


class World:
    """ECS 월드: 엔티티, 컴포넌트, 시스템을 관리하며 계약을 검증한다."""

    def __init__(self):
        self.entities = ValidatedStore()
        self.components = ValidatedStore()
        self.systems = []
        self._has_run = False

    def add_entity(self, name: str, entity) -> 'World':
        if name in self.entities:
            raise ValueError(f"엔티티 '{name}'가 이미 등록되어 있습니다.")
        self.entities[name] = entity
        return self

    def add_component(self, name: str, component) -> 'World':
        if name in self.components:
            raise ValueError(f"컴포넌트 '{name}'가 이미 등록되어 있습니다.")
        self.components[name] = component
        return self

    def add_system(self, system: System) -> 'World':
        if any(type(s) is type(system) for s in self.systems):
            raise ValueError(f"{type(system).__name__}가 이미 등록되어 있습니다.")
        self.systems.append(system)
        return self

    def run(self) -> None:
        if self._has_run:
            raise RuntimeError("World.run()은 한 번만 호출할 수 있습니다.")
        self._has_run = True

        logger.info("파이프라인 실행 시작 (%d개 시스템)", len(self.systems))
        for system in self.systems:
            self._validate(system.requires_entities, self.entities, system, "엔티티 입력 누락")
            self._validate(system.requires_components, self.components, system, "컴포넌트 입력 누락")

            try:
                system.execute(self.entities, self.components)
            except Exception as e:
                raise RuntimeError(f"[{type(system).__name__}] 실행 중 오류: {e}") from e

            self._validate(system.produces_entities, self.entities, system, "엔티티 출력 누락")
            self._validate(system.produces_components, self.components, system, "컴포넌트 출력 누락")
        logger.info("파이프라인 실행 완료")

    def _validate(self, required: frozenset, store: dict, system: System, msg: str):
        missing = required - store.keys()
        if missing:
            raise RuntimeError(f"[{type(system).__name__}] {msg}: {sorted(missing)}")