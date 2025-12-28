class PreRunSetup:
    def __init__(self, dialogs, state, logger):
        self.dialogs = dialogs
        self.state = state
        self.log = logger

    def run(self) -> bool:
        alignment = self.dialogs.select_alignment()
        if alignment is None:
            self.log("노선 선택 취소")
            return False

        self.state.alignment_type = alignment

        exists, value = self.dialogs.ask_brokenchain()
        self.state.isbrokenchain = exists
        self.state.brokenchain = value if exists else 0.0

        offset = self.dialogs.show_input_float(title='오프셋 입력',prompt='오프셋 값을 입력하세요.')
        if offset is None:
            offset = 0.0
        self.state.offset = offset

        posttype = self.dialogs.show_select_function()
        if posttype is None:
            return False
        self.state.posttype = posttype

        #복선 여부 확인후 선로간격 입력받기
        if self.state.is_two_track:
            track_distance = self.dialogs.show_input_float(title='선로중심간격 입력',prompt='선로 중심간격을 입력하세요.')
            if track_distance is None:
                return False
            self.state.track_distance = track_distance
        return True
