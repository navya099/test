from math_utils import degrees_to_dms
from model.ipdata import IPdata
import math

class IPTableDrawer:
    def __init__(self, msp):
        self.msp = msp

    def draw_ip_table(self, iplist: list[IPdata]):
        for i, ip in enumerate(iplist):
            if i != 0 and i != len(iplist) - 1:

                iatext = degrees_to_dms(math.degrees(ip.ia))
                cl_value = max(
                    getattr(seg, "total_length", getattr(seg, "length", 0))
                    for seg in ip.segment
                )
                radius = f'{ip.radius:.3f}'
                tl = max(seg.tl for seg in ip.segment)
                tl = f'{tl:.3f}'
                cl = f'{cl_value:.3f}'
                x = f'{ip.coord.y:.4f}'
                y = f'{ip.coord.x:.4f}'
                block_ref = self.msp.add_blockref(
                    name="IPTABLE",
                    insert=(ip.coord.x, ip.coord.y),
                    dxfattribs={
                        "layer": "IPTABLE"
                    }
                )
                block_ref.add_auto_attribs({
                        "IPNO": f'IP. {ip.ipno}' if isinstance(ip.ipno, int) else ip.ipno,
                        "IA": iatext,
                        "R": radius,
                        "TL": tl,
                        "CL": cl,
                        "X": x,
                        "Y": y
                })