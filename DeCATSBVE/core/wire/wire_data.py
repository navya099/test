from dataclasses import dataclass, field

from core.insulator.insulator_data import InsulatorData
from core.wire.singlewire import SingleWire


@dataclass
class WireData:
    """한 pos에 여러 wire를 담는 컨테이너"""
    pos: int
    span: int
    wires: list[SingleWire]
    track_name: str
    insulators: list[InsulatorData] = field(default_factory=list) # 리스트로 변경

    def add_wire(self, wire: SingleWire):
        self.wires.append(wire)

    def add_insulator(self, insulator: InsulatorData):
        self.insulators.append(insulator)
