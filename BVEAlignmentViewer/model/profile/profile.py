from model.profile.profileentity import ProfileEntity
from model.profile.profileentitycollection import ProfileEntityCollection
from model.profile.profilepvicollection import ProfilePVICollection


class Profile:
    """
    A record of elevation against distance along a horizontal Alignment or other line. Profiles are used to visualize the terrain along a route of interest, such as a proposed road, or simply to show how the elevation changes across a particular region.
    """
    def __init__(self, name: str):
        self.name: str = name
        self.pvis: ProfilePVICollection = ProfilePVICollection()
        self.entities: ProfileEntityCollection = ProfileEntityCollection()

    @property
    def max_slope(self):
        gradin = max((pvi.gradein for pvi in self.pvis), default=0.0)
        gradeout = max((pvi.gradeout for pvi in self.pvis), default=0.0)
        return max(gradin, gradeout)

    @property
    def min_slope(self):
        gradin = min((pvi.gradein for pvi in self.pvis), default=0.0)
        gradeout = min((pvi.gradeout for pvi in self.pvis), default=0.0)
        return min(gradin, gradeout)

    @property
    def max_elevation(self):
        return max((pvi.elevation for pvi in self.pvis), default=0.0)

    @property
    def min_elevation(self):
        return min((pvi.elevation for pvi in self.pvis), default=0.0)

    @property
    def start_station(self):
        return self.pvis[0].station if self.pvis else 0.0

    @property
    def end_station(self):
        return self.pvis[-1].station if self.pvis else 0.0

    @property
    def length(self):
        return self.end_station - self.start_station if self.pvis else 0.0

    def elevation_at_station(self, station: float) -> float:
        """
        해당 측점에서의 고도 반환
        Args:
            station:

        Returns:
            elevation: float
        """
        for pvi in self.pvis:
            if pvi.station == station:
                return pvi.elevation
        return 0.0


