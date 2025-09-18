from dataclasses import dataclass

from Profile.profileentity import ProfileEntity

@dataclass
class ProfileTangent(ProfileEntity):
    grade: float = 0.0
