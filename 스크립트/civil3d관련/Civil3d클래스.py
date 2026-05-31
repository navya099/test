# Base classes (간단화된 형태)
from enum import Enum


class RXObject:
    pass


class DBObject(RXObject):
    pass


class Entity(DBObject):
    def __init__(self):
        self.Name = ""
        self.Description = ""


# Feature 클래스
class Feature(Entity):
    def __init__(self):
        super().__init__()


class AlignmentType(Enum):
    Centerline = 1
    Offset = 2
    CurbReturn = 3
    Utility = 4
    Rail = 5

# Alignment 클래스
class Alignment(Feature):
    def __init__(self):
        super().__init__()
        self.AlignmentType = ''
        self.Entities = AlignmentEntityCollection()
        self.StartingStation = 0.0
        self.EndingStation = 0.0
        self.Length = 0.0

    def Create(self):
        raise NotImplementedError


# AlignmentEntityCollection 및 엔티티 클래스
class AlignmentEntity:
    def __init__(self):
        self.StartStation = 0.0
        self.EndStation = 0.0


class AlignmentEntityCollection:
    def __init__(self):
        self._entities = []

    def Add(self, entity: AlignmentEntity):
        self._entities.append(entity)

    def __iter__(self):
        return iter(self._entities)

    def __len__(self):
        return len(self._entities)

    def __getitem__(self, index):
        return self._entities[index]
