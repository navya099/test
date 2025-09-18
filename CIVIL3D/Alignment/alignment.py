from Alignment.alignmententitycollection import AlignmentEntityCollection
from Alignment.alignmenttype import AlignmentType


class Alignment:
    """
    Alignment 클래스. Alignment 객체는 중심선, 차선, 갓길, 통행권 또는 시공 기준선을 나타낼 수 있습니다.
    """

    def __init__(self, name: str = "", display_name: str = "",
                 alignment_type: AlignmentType = AlignmentType.Centerline):
        self.alignment_type: AlignmentType = alignment_type
        self.display_name: str = display_name or name
        self.name: str = name
        self.entities: AlignmentEntityCollection = AlignmentEntityCollection()

    @property
    def starting_station(self) -> float | None:
        if not self.entities:
            raise ValueError("No entities in alignment")
        return self.entities[0].starting_station

    @property
    def ending_station(self) -> float | None:
        if not self.entities:
            raise ValueError("No entities in alignment")
        return self.entities[-1].ending_station

    @property
    def length(self) -> float:
        if self.starting_station is None or self.ending_station is None:
            return 0.0
        return self.ending_station - self.starting_station

    @classmethod
    def create(cls, alignmentname: str) -> "Alignment":
        """기하구조 없이 alignmentname으로 선형 생성"""
        return cls(name=alignmentname, display_name=alignmentname)

    def distance_to_alignment(self, alignment: "Alignment") -> float:
        """
        다른 정렬까지의 거리를 계산합니다. 대상 정렬이 현재 정렬과 교차하는 경우, 이 메서드는 양쪽에서 대상 정렬까지의 거리를 확인하고 더 짧은 거리를 반환합니다.
        Returns:
            distance: float
        """
        raise NotImplementedError("distance_to_alignment is not yet implemented")

    def get_instantaneous_radius(self, station: float) -> float:
        """
        지정된 측점에서 순간 반경을 반환합니다.

        Parameters
        ----------
        station : float
            계산 대상 측점

        Returns
        -------
        float
            반경 값
        """
        raise NotImplementedError("get_instantaneous_radius is not yet implemented")

    def get_profile_ids(self):
        """
        이 정렬에 속하는 모든 프로필의 ObjectIdCollection을 가져옵니다.
        Returns:

        """
        raise NotImplementedError("get_profile_ids is not yet implemented")

    def point_location(self, station: float, offset: float) -> tuple[float, float]:
        """
        스테이션과 정렬에 대한 오프셋이 주어지면 정렬 상의 지점의 동쪽과 북쪽을 반환합니다.
        Returns:
            tuple[north: float, south: float]
        """
        raise NotImplementedError("point_location is not yet implemented")

    def reverse(self):
        """
        정렬을 뒤집습니다.
        """
        raise NotImplementedError("reverse is not yet implemented")

    def station_offset(self, easting: float, northing: float) -> tuple[float, float]:
        """
        주어진 동쪽 및 북쪽 값에서 정렬에 대한 스테이션과 오프셋을 반환합니다.
        Returns:
            station: float
            offset: float

        """
        raise NotImplementedError("station_offset is not yet implemented")
