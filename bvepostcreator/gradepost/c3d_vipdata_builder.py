from gradepost.vip_builder import VIPDATABuilder
import pandas as pd

from model.grade.vipdata import VIPdata


class C3DVIPDATABuilder(VIPDATABuilder):
    """CIVIL3D용 VIP데이터 빌더"""
    def preprocess(self, data, brokenchain):
        """전처리(CIVIL3D에서는 안함)"""
        return data

    def build(self, data, brokenchain):

        df = pd.read_excel(data, header=0)

        vip_list = []
        current_ip = None
        ip_counter = 1

        for _, row in df.iterrows():
            number = row['번호'] if pd.notna(row['번호']) else 0
            vipsta = row['PVI 측점'] if pd.notna(row['PVI 측점']) else 0.0
            prev_pitch = row['종단 진입부 경사'] if pd.notna(row['종단 진입부 경사']) else 0.0
            next_pitch = row['종단 진출부 경사'] if pd.notna(row['종단 진출부 경사']) else 0.0
            seg = row['종단 원곡선 유형'].strip() if pd.notna(row['종단 원곡선 유형']) else ''
            vlength = row['종단 원곡선 길이'] if pd.notna(row['종단 원곡선 길이']) else 0.0
            vradius = row['원곡선 반지름'] if pd.notna(row['원곡선 반지름']) else 0.0
            isverticalvurve = True if seg == '볼록형' or seg == '오목형' else False

            # 파정 적용
            vipsta += brokenchain
            if current_ip:  # 이전 IP 저장
                vip_list.append(current_ip)
            current_ip = VIPdata(VIPNO=ip_counter)
            ip_counter += 1
            current_ip.VIP_STA = vipsta
            current_ip.seg = seg
            current_ip.vradius = vradius
            current_ip.isvcurve = isverticalvurve
            current_ip.vlength = vlength
            current_ip.prev_slope = prev_pitch * 0.001  # 퍼밀을 0..01로 변환
            current_ip.next_slope = next_pitch * 0.001  # 퍼밀을 0..01로 변환
            # bvc evc 계산
            current_ip.BVC_STA = vipsta - (vlength / 2)  # BVC
            current_ip.EVC_STA = vipsta + (vlength / 2)  # EVC

        return vip_list
