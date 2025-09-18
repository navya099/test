from core.profile.profileprocessor import ProfileProcessor
from model.bveroutedata import BVERouteData
from Profile.profile import Profile


class ProfileBuilder:
    """
    종단 생성 stateless 클래스
    """
    @staticmethod
    def build_profile(bvedata: BVERouteData) -> Profile:
        """
        bvedata로부터 종단 객체를 생성하는 메소드
        Returns:
            Profile
        """
        profile = ProfileProcessor.proceess_profile(bvedata)
        return profile