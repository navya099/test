from typing import List
import csv
from alignment.pipoint import PIPoint
from profile.pvi import PVIPoint
from superelevation.superelevation import SuperelevationStation
from superelevation.superelevation_table import SuperelevationTable


class CSVDesignSpecLoader:
    """
    CSV 설계 제원 로더
    """
    @staticmethod
    def load_pis_from_csv(filepath: str) -> List[PIPoint]:
        """CSV로부터 piPOINT 생성"""
        pis = []
        with open(filepath, mode="r", encoding="utf-8-sig") as f:

            for row in csv.DictReader(f):
                def flt(val):
                    return float(val) if val and val.strip() != "" else None

                pis.append(PIPoint(
                    name=row["Name"].strip(),
                    easting=float(row["Easting"]),
                    northing=float(row["Northing"]),
                    R=float(row["R"] or 0.0),
                    L1=flt(row.get("L1")), L2=flt(row.get("L2")),
                    A1=flt(row.get("A1")), A2=flt(row.get("A2"))
                ))
        return pis

    @staticmethod
    def load_pvis_from_csv(filepath: str) -> List:
        """CSV로부터 pViPOINT 생성"""
        pvis = []
        with open(filepath, mode="r", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                def flt(val):
                    return float(val) if val and val.strip() != "" else None

                pvis.append(PVIPoint(
                    name=row["Name"].strip(),
                    station=float(row["RawStation"]),
                    elevation=float(row["Elevation"]),
                    L=flt(row.get("L")), L1=flt(row.get("L1")), L2=flt(row.get("L2"))
                ))
        return pvis

    @staticmethod
    def load_super_from_csv(filepath: str) -> SuperelevationTable:
        """CSV로부터 SuperelevationTable 생성"""
        stations = []
        with open(filepath, mode="r", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                stations.append(SuperelevationStation(
                    station=float(row["RawStation"]),
                    left_slope=float(row["LeftSlope"]),
                    right_slope=float(row["RightSlope"])
                ))
        return SuperelevationTable(stations)