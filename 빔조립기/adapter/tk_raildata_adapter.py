from adapter.tk_bracket_adapter import TKBracketAdapter
from model.rail import RailData
from model.tkraildata import TKRailData
from vector3 import Vector3
import tkinter as tk
import uuid

class TKRaildataAdapter:
    @staticmethod
    def collect(rails: list[TKRailData]):
        result =[]
        for rail in rails:
            index = rail.index
            name= rail.name
            coord = Vector3(
                rail.coordx.get(),rail.coordy.get(),rail.coordz.get()
            )
            brackets = []
            for b in rail.brackets:
                brackets.append(
                    TKBracketAdapter.from_vm(b, rail.index)
                )
            result.append(
                RailData(
                    index=index,
                    name=name,
                    coord=coord,
                    brackets=brackets,
                    uid=rail.uid
                )
            )
        return result

    @staticmethod
    def from_dto(data: RailData) -> TKRailData:
        return TKRailData(
            index_var=tk.IntVar(value=data.index),
            name_var=tk.StringVar(value=data.name),
            brackets=data.brackets,
            coordx=tk.DoubleVar(value=data.coord.x),
            coordy=tk.DoubleVar(value=data.coord.y),
            coordz=tk.DoubleVar(value=data.coord.z),
            uid=data.uid
        )
