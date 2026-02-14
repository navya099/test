from dataclasses import dataclass

from core.wire.singlewire import SingleWire


@dataclass
class WireData:
    """한 pos에 여러 wire를 담는 컨테이너"""
    pos: int
    span: int
    wires: list[SingleWire]
    track_name: str
    def add_wire(self, wire: SingleWire):
        self.wires.append(wire)