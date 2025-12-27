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

        offset = self.dialogs.ask_offset()
        if offset is None:
            offset = 0.0
        self.state.offset = offset

        posttype = self.dialogs.show_select_function()
        if posttype is None:
            return False
        self.state.posttype = posttype

        return True
