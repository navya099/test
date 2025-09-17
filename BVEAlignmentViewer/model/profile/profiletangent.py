from dataclasses import dataclass

from model.profile.profileentity import ProfileEntity

@dataclass
class ProfileTangent(ProfileEntity):
    grade: float = 0.0
