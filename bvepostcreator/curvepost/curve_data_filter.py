from curvepost.curve_util import get_curve_lines


class CurveDataFilter:
    def __init__(self, log):
        self.log = log

    def filter(self, ipdatas, start, end):
        valid_ips = []
        for ip in ipdatas:
            if ip.SP_STA is None and ip.BC_STA is None:
                self.log("STA 값 없음")
                continue
            sp_in_range = (ip.SP_STA is not None and start <= ip.SP_STA <= end)
            bc_in_range = (ip.BC_STA is not None and start <= ip.BC_STA <= end)
            if not (sp_in_range or bc_in_range):
                self.log("범위를 벗어났습니다.")
                continue
            lines = get_curve_lines(ip)
            if not lines:
                self.log("데이터 없음")
                continue
            valid_ips.append((ip, lines))
        return valid_ips
