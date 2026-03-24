class PreRunSetup:
    def __init__(self, dialogs, state, logger):
        self.dialogs = dialogs
        self.state = state
        self.log = logger

    def run(self) -> bool:
        try:
            self.preset_alignment_type()
            self.preset_posttype()
            return True
        except Exception as e:
            self.log.error(e)
            return False

    def preset_alignment_type(self):
        alignment = self.dialogs.select_option_list(['도시철도', '일반철도', '준고속철도', '고속철도'])
        if alignment is None:
            self.log("노선 선택 취소")
            return
        self.state.alignment_type = alignment

    def preset_posttype(self):
        posttype = self.dialogs.select_option_list(['거리표', '곡선표', '기울기표', '구조물표'])
        if posttype is None:
            return
        self.state.posttype = posttype