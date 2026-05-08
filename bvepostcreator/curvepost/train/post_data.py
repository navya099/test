class TrainPostData:
    """철도용 포스트 데이터 객체"""
    def __init__(self, curvetype: str, station: str, cant: str, filename: str):
        self.curvetype = curvetype
        self.station = station
        self.cant = cant
        self.filename = filename
