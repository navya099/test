import logging

class RailLoader:
    """다중 선로 로더 클래스"""
    def __init__(self):
        self.filepath = ''
        self.tracks = {}  # {track_no: [(x, z, y), ...]}

    def load(self, filepath):
        """rail.info 파일을 읽고 트랙 딕셔너리 반환"""
        self.filepath = filepath
        raw_data = self.read_railinfo()
        self.fillter_rail(raw_data)
        return self.tracks

    def read_railinfo(self):
        """rail.info 파일을 읽어서 원본 리스트 반환"""
        data = []
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split(',')
                    if len(parts) != 5:
                        continue
                    track_no = int(parts[0])
                    x = float(parts[1])
                    y = float(parts[2])
                    z = float(parts[3])
                    station = float(parts[4])
                    data.append((track_no, x, y, z, station))
            logging.info(f"Rail info 읽기 완료: {len(data)} rows")
        except Exception as e:
            logging.error(f"Rail info 읽기 실패: {e}")
            raise e
        return data

    def fillter_rail(self, raw_data):
        """선로번호별로 필터링하여 self.tracks에 저장"""
        for track_no, x, y, z, sta in raw_data:
            if track_no not in self.tracks:
                self.tracks[track_no] = []
            self.tracks[track_no].append((x, y, z, sta))
        logging.info(f"Rail info 필터링 완료: {len(self.tracks)} tracks")
