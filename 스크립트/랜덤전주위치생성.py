import random
import os
import pandas as pd
import tkinter as tk
from tkinter import filedialog
import math
import re
import numpy as np
from enum import Enum
from shapely.geometry import Point, LineString
import ezdxf  # Import ezdxf for saving to DXF

'''
ver 2025.03.19
종단면도작성기능 추가(진행중)
#modify

'''


class AirJoint(Enum):
    START = "에어조인트 시작점 (1호주)"
    POINT_2 = "에어조인트 (2호주)"
    MIDDLE = "에어조인트 중간주 (3호주)"
    POINT_4 = "에어조인트 (4호주)"
    END = "에어조인트 끝점 (5호주)"


def create_new_dxf():
    doc = ezdxf.new()
    msp = doc.modelspace()

    return doc, msp


def crate_pegging_plan_mast_and_bracket(doc, msp, polyline, positions, structure_list, curve_list, pitchlist,
                                        airjoint_list):
    post_number_lst = generate_postnumbers(positions)
    polyline_with_sta = [(i * 25, *values) for i, values in enumerate(polyline)]

    # 전주 데이터 구성
    pole_data = format_pole_data(DESIGNSPEED)

    for i in range(len(positions) - 1):
        pos, next_pos = positions[i], positions[i + 1]
        currentspan = next_pos - pos  # 현재 경간
        current_structure = isbridge_tunnel(pos, structure_list)  # 현재 구조물
        current_curve, R, c = iscurve(pos, curve_list)  # 현재 곡선
        current_slope, pitch = isslope(pos, pitchlist)  # 현재 구배
        current_airjoint = check_isairjoint(pos, airjoint_list)  # 현재 에어조인트
        post_number = find_post_number(post_number_lst, pos)  # 전주번호
        gauge = get_pole_gauge(DESIGNSPEED, current_structure)  # 구조물 offset
        _, mast_name = get_mast_type(DESIGNSPEED, current_structure)
        # 해당 구조물에 대한 전주 데이터 가져오기 (없으면 '토공' 기본값 사용)
        station_data = pole_data.get(current_structure, pole_data.get('토공', {}))

        # '교량' 같은 구간일 경우, 곡선 여부에 따라 데이터 선택
        if isinstance(station_data, dict) and '직선' in station_data:
            station_data = station_data.get('곡선' if current_curve == '곡선' else '직선', {})

        # 필요한 데이터 추출 (기본값 설정)
        I_type = station_data.get('I_type', '기본_I_type')
        O_type = station_data.get('O_type', '기본_O_type')
        I_bracket = station_data.get('I_bracket', '기본_I_bracket')
        O_bracket = station_data.get('O_bracket', '기본_O_bracket')

        # 홀수/짝수에 맞는 전주 데이터 생성
        pole_type = I_type if i % 2 == 1 else O_type
        bracket_type = I_bracket if i % 2 == 1 else O_bracket

        # 전주 좌표 반환
        pos_coord, vector_pos = return_pos_coord(polyline_with_sta, pos)  # 전주 측점 좌표와 벡터
        # offset 적용 좌표
        pos_coord_with_offset = calculate_offset_point(vector_pos, pos_coord, gauge)
        char_height = 3 * H_scale

        if current_airjoint:
            """에어조인트 각 구간별 브래킷 추가"""
            if current_airjoint == AirJoint.START.value:
                # 브래킷텍스트
                msp.add_mtext(f"{post_number}\n{pos}\n{bracket_type}\n{mast_name}",
                              dxfattribs={'insert': pos_coord_with_offset, 'char_height': char_height, 'layer': '브래킷',
                                          'color': 6})
                msp.add_line(pos_coord, pos_coord_with_offset, dxfattribs={'layer': '브래킷', 'color': 6})
            elif current_airjoint == AirJoint.POINT_2.value:
                first_bracetl_pos = pos - 0.5
                second_brakcet_pos = pos + 0.5

                first_bracetl_coord, first_bracetl_vector = return_pos_coord(polyline_with_sta,
                                                                             first_bracetl_pos)  # 전주 측점 좌표와 벡터
                second_bracetl_coord, second_bracetl_vector = return_pos_coord(polyline_with_sta,
                                                                               second_brakcet_pos)  # 전주 측점 좌표와 벡터

                first_bracetl_coord_with_offset = calculate_offset_point(first_bracetl_vector, first_bracetl_coord,
                                                                         gauge)
                second_bracetl_coord_with_offset = calculate_offset_point(second_bracetl_vector, second_bracetl_coord,
                                                                          gauge)
                # 브래킷 텍스트
                msp.add_mtext(f"{post_number}\n{pos}\nF(S), AJ-I\n{mast_name}",
                              dxfattribs={'insert': pos_coord_with_offset, 'char_height': char_height, 'layer': '브래킷',
                                          'color': 6})

                msp.add_line(first_bracetl_coord, first_bracetl_coord_with_offset,
                             dxfattribs={'layer': '브래킷', 'color': 6})
                msp.add_line(second_bracetl_coord, second_bracetl_coord_with_offset,
                             dxfattribs={'layer': '브래킷', 'color': 6})

            elif current_airjoint == AirJoint.MIDDLE.value:
                # MIDDLE 구간 처리
                first_bracetl_pos = pos - 0.8
                second_brakcet_pos = pos + 0.8

                first_bracetl_coord, first_bracetl_vector = return_pos_coord(polyline_with_sta,
                                                                             first_bracetl_pos)  # 전주 측점 좌표와 벡터
                second_bracetl_coord, second_bracetl_vector = return_pos_coord(polyline_with_sta,
                                                                               second_brakcet_pos)  # 전주 측점 좌표와 벡터

                first_bracetl_coord_with_offset = calculate_offset_point(first_bracetl_vector, first_bracetl_coord,
                                                                         gauge)
                second_bracetl_coord_with_offset = calculate_offset_point(second_bracetl_vector, second_bracetl_coord,
                                                                          gauge)

                # 브래킷 텍스트
                msp.add_mtext(f"{post_number}\n{pos}\nAJ-O, AJ-O\n{mast_name}",
                              dxfattribs={'insert': pos_coord_with_offset, 'char_height': char_height, 'layer': '브래킷',
                                          'color': 6})

                msp.add_line(first_bracetl_coord, first_bracetl_coord_with_offset,
                             dxfattribs={'layer': '브래킷', 'color': 6})
                msp.add_line(second_bracetl_coord, second_bracetl_coord_with_offset,
                             dxfattribs={'layer': '브래킷', 'color': 6})

            elif current_airjoint == AirJoint.POINT_4.value:
                first_bracetl_pos = pos - 0.5
                second_brakcet_pos = pos + 0.5

                first_bracetl_coord, first_bracetl_vector = return_pos_coord(polyline_with_sta,
                                                                             first_bracetl_pos)  # 전주 측점 좌표와 벡터
                second_bracetl_coord, second_bracetl_vector = return_pos_coord(polyline_with_sta,
                                                                               second_brakcet_pos)  # 전주 측점 좌표와 벡터

                first_bracetl_coord_with_offset = calculate_offset_point(first_bracetl_vector, first_bracetl_coord,
                                                                         gauge)
                second_bracetl_coord_with_offset = calculate_offset_point(second_bracetl_vector, second_bracetl_coord,
                                                                          gauge)

                msp.add_line(first_bracetl_coord, first_bracetl_coord_with_offset,
                             dxfattribs={'layer': '브래킷', 'color': 6})
                msp.add_line(second_bracetl_coord, second_bracetl_coord_with_offset,
                             dxfattribs={'layer': '브래킷', 'color': 6})

                # 브래킷 텍스트
                msp.add_mtext(f"{post_number}\n{pos}\nAJ-O, F(L)\n{mast_name}",
                              dxfattribs={'insert': pos_coord_with_offset, 'char_height': char_height, 'layer': '브래킷',
                                          'color': 6})

            elif current_airjoint == AirJoint.END.value:
                # 브래킷텍스트
                msp.add_mtext(f"{post_number}\n{pos}\n{bracket_type}\n{mast_name}",
                              dxfattribs={'insert': pos_coord_with_offset, 'char_height': char_height, 'layer': '브래킷',
                                          'color': 6})
                # 브래킷
                msp.add_line(pos_coord, pos_coord_with_offset, dxfattribs={'layer': '브래킷', 'color': 6})
        else:
            # 브래킷
            msp.add_line(pos_coord, pos_coord_with_offset, dxfattribs={'layer': '브래킷', 'color': 6})
            # 브래킷텍스트
            msp.add_mtext(f"{post_number}\n{pos}\n{bracket_type}\n{mast_name}",
                          dxfattribs={'insert': pos_coord_with_offset, 'char_height': char_height, 'layer': '브래킷',
                                      'color': 6})

        # 전주번호
        # msp.add_text(post_number, dxfattribs={'insert':pos_coord_with_offset, 'height': 3, 'layer': '전주번호', 'color' : 4})
        # 전주
        msp.add_circle(pos_coord_with_offset, radius=1.5 * H_scale, dxfattribs={'layer': '전주', 'color': 4})

    # 선형 플롯
    polyline_points = [(point[1], point[2]) for point in polyline_with_sta]
    msp.add_lwpolyline(polyline_points, close=False, dxfattribs={'layer': '선형', 'color': 1})

    return doc, msp


def crate_pegging_plan_wire(doc, msp, polyline, positions, structure_list, curve_list, pitchlist, airjoint_list):
    post_number_lst = generate_postnumbers(positions)
    polyline_with_sta = [(i * 25, *values) for i, values in enumerate(polyline)]

    # 전주 데이터 구성
    pole_data = format_pole_data(DESIGNSPEED)

    x, y = get_bracket_coordinates(DESIGNSPEED, 'AJ형_시점')
    x1, y1 = get_bracket_coordinates(DESIGNSPEED, 'F형_시점')
    x2, y2 = get_bracket_coordinates(DESIGNSPEED, 'AJ형_중간1')
    x3, y3 = get_bracket_coordinates(DESIGNSPEED, 'AJ형_중간2')
    x4, y4 = get_bracket_coordinates(DESIGNSPEED, 'AJ형_끝')
    x5, y5 = get_bracket_coordinates(DESIGNSPEED, 'F형_끝')

    for i in range(len(positions) - 1):
        pos, next_pos = positions[i], positions[i + 1]
        currentspan = next_pos - pos  # 현재 경간
        current_structure = isbridge_tunnel(pos, structure_list)  # 현재 구조물
        next_structure = isbridge_tunnel(next_pos, structure_list)
        current_curve, R, c = iscurve(pos, curve_list)  # 현재 곡선
        current_slope, pitch = isslope(pos, pitchlist)  # 현재 구배
        current_airjoint = check_isairjoint(pos, airjoint_list)  # 현재 에어조인트
        post_number = find_post_number(post_number_lst, pos)  # 전주번호
        gauge = get_pole_gauge(DESIGNSPEED, current_structure)  # 구조물 offset
        next_gauge = get_pole_gauge(DESIGNSPEED, next_structure)  # 다음 구조물 offset
        _, mast_name = get_mast_type(DESIGNSPEED, current_structure)  # 전주형식
        # 해당 구조물에 대한 전주 데이터 가져오기 (없으면 '토공' 기본값 사용)
        station_data = pole_data.get(current_structure, pole_data.get('토공', {}))

        # '교량' 같은 구간일 경우, 곡선 여부에 따라 데이터 선택
        if isinstance(station_data, dict) and '직선' in station_data:
            station_data = station_data.get('곡선' if current_curve == '곡선' else '직선', {})

        # 필요한 데이터 추출 (기본값 설정)
        I_type = station_data.get('I_type', '기본_I_type')
        O_type = station_data.get('O_type', '기본_O_type')
        I_bracket = station_data.get('I_bracket', '기본_I_bracket')
        O_bracket = station_data.get('O_bracket', '기본_O_bracket')

        # 홀수/짝수에 맞는 전주 데이터 생성
        pole_type = I_type if i % 2 == 1 else O_type
        bracket_type = I_bracket if i % 2 == 1 else O_bracket

        # 편위와 직선구간 각도
        current_stagger, _ = get_lateral_offset_and_angle(i, currentspan)
        next_stagger, _ = get_lateral_offset_and_angle(i + 1, currentspan)

        # 전주 좌표 반환
        pos_coord, vector_pos = return_pos_coord(polyline_with_sta, pos)  # 전주 측점 좌표와 벡터
        next_coord, next_vector = return_pos_coord(polyline_with_sta, next_pos)  # 전주 측점 좌표와 벡터

        # 전선 시점 좌표
        wire_coord = calculate_offset_point(vector_pos, pos_coord, current_stagger)
        next_wire_coord = calculate_offset_point(next_vector, next_coord, next_stagger)

        if current_airjoint:
            """에어조인트 각 구간별 브래킷 추가"""
            if current_airjoint == AirJoint.START.value:
                # 무효선
                inactive_wire_start_coord = calculate_offset_point(vector_pos, pos_coord, gauge)
                inactive_wire_end_coord = calculate_offset_point(next_vector, next_coord, x1)
                msp.add_line(inactive_wire_start_coord, inactive_wire_end_coord,
                             dxfattribs={'layer': '전차선', 'color': 3})

                # 본선
                wire_end_coord = calculate_offset_point(next_vector, next_coord, x)
                msp.add_line(wire_coord, wire_end_coord, dxfattribs={'layer': '전차선', 'color': 3})
            elif current_airjoint == AirJoint.POINT_2.value:
                # 무효선
                inactive_wire_start_coord = calculate_offset_point(vector_pos, pos_coord, x1)
                inactive_wire_end_coord = calculate_offset_point(next_vector, next_coord, x2)
                msp.add_line(inactive_wire_start_coord, inactive_wire_end_coord,
                             dxfattribs={'layer': '전차선', 'color': 3})

                # 본선
                wire_start_coord = calculate_offset_point(vector_pos, pos_coord, x)
                wire_end_coord = calculate_offset_point(next_vector, next_coord, x3)
                msp.add_line(wire_start_coord, wire_end_coord, dxfattribs={'layer': '전차선', 'color': 3})

            elif current_airjoint == AirJoint.MIDDLE.value:
                # 무효선
                inactive_wire_start_coord = calculate_offset_point(vector_pos, pos_coord, x2)
                inactive_wire_end_coord = calculate_offset_point(next_vector, next_coord, x4)
                msp.add_line(inactive_wire_start_coord, inactive_wire_end_coord,
                             dxfattribs={'layer': '전차선', 'color': 3})

                # 본선
                wire_start_coord = calculate_offset_point(vector_pos, pos_coord, x3)
                wire_end_coord = calculate_offset_point(next_vector, next_coord, x5)
                msp.add_line(wire_start_coord, wire_end_coord, dxfattribs={'layer': '전차선', 'color': 3})

            elif current_airjoint == AirJoint.POINT_4.value:
                # 무효선
                inactive_wire_start_coord = calculate_offset_point(vector_pos, pos_coord, x5)
                inactive_wire_end_coord = calculate_offset_point(next_vector, next_coord, next_gauge)
                msp.add_line(inactive_wire_start_coord, inactive_wire_end_coord,
                             dxfattribs={'layer': '전차선', 'color': 3})

                # 본선
                wire_start_coord = calculate_offset_point(vector_pos, pos_coord, x4)
                wire_end_coord = calculate_offset_point(next_vector, next_coord, next_stagger)
                msp.add_line(wire_start_coord, wire_end_coord, dxfattribs={'layer': '전차선', 'color': 3})
            elif current_airjoint == AirJoint.END.value:
                msp.add_line(wire_coord, next_wire_coord, dxfattribs={'layer': '전차선', 'color': 3})
        else:
            msp.add_line(wire_coord, next_wire_coord, dxfattribs={'layer': '전차선', 'color': 3})
    return doc, msp


def draw_feeder_wire_plan(msp, pos_coord, end_pos, current_structure, next_structure):
    pass


def create_pegging_profile_mast_and_bracket(doc, msp, polyline, positions, structure_list, curve_list, pitchlist,
                                            airjoint_list):
    post_number_lst = generate_postnumbers(positions)
    polyline_with_sta = [(i * 25, *values) for i, values in enumerate(polyline)]

    # 전주 데이터 구성
    pole_data = format_pole_data(DESIGNSPEED)

    char_height = 3 * H_scale
    for i in range(len(positions) - 1):
        pos, next_pos = positions[i], positions[i + 1]
        currentspan = next_pos - pos  # 현재 경간
        current_structure = isbridge_tunnel(pos, structure_list)  # 현재 구조물
        next_structure = isbridge_tunnel(next_pos, structure_list)  # 다음 구조물
        current_curve, R, c = iscurve(pos, curve_list)  # 현재 곡선
        current_slope, pitch = isslope(pos, pitchlist)  # 현재 구배
        current_airjoint = check_isairjoint(pos, airjoint_list)  # 현재 에어조인트
        current_pos_z = get_elevation_pos(pos, polyline_with_sta)  # 현재 전주의 z값
        next_pos_z = get_elevation_pos(next_pos, polyline_with_sta)  # 다음 전주의 z값
        post_number = find_post_number(post_number_lst, pos)  # 전주번호
        gauge = get_pole_gauge(DESIGNSPEED, current_structure)  # 구조물 offset
        _, mast_name = get_mast_type(DESIGNSPEED, current_structure)
        _, _, current_system_height, current_contact_height = get_contact_wire_and_massanger_wire_info(DESIGNSPEED,
                                                                                                       current_structure,
                                                                                                       currentspan)
        _, _, next_system_height, next_contact_height = get_contact_wire_and_massanger_wire_info(DESIGNSPEED,
                                                                                                 next_structure,
                                                                                                 currentspan)
        _, _, h1, h2, _, _ = initialrize_tenstion_device(pos, gauge, currentspan, current_contact_height,
                                                         current_system_height)
        h1 = h1 * V_scale
        h2 = h2 * V_scale

        # 스케일 적용된 높이
        # 스케일 적용된 높이 변환 (리스트 활용)
        current_system_height, current_contact_height, next_system_height, next_contact_height = [
            height * V_scale for height in
            (current_system_height, current_contact_height, next_system_height, next_contact_height)
        ]

        # 해당 구조물에 대한 전주 데이터 가져오기 (없으면 '토공' 기본값 사용)
        station_data = pole_data.get(current_structure, pole_data.get('토공', {}))

        # '교량' 같은 구간일 경우, 곡선 여부에 따라 데이터 선택
        if isinstance(station_data, dict) and '직선' in station_data:
            station_data = station_data.get('곡선' if current_curve == '곡선' else '직선', {})

        # 필요한 데이터 추출 (기본값 설정)
        I_type = station_data.get('I_type', '기본_I_type')
        O_type = station_data.get('O_type', '기본_O_type')
        I_bracket = station_data.get('I_bracket', '기본_I_bracket')
        O_bracket = station_data.get('O_bracket', '기본_O_bracket')

        # 홀수/짝수에 맞는 전주 데이터 생성
        pole_type = I_type if i % 2 == 1 else O_type
        bracket_type = I_bracket if i % 2 == 1 else O_bracket

        # 전주 좌표 반환
        pos_coord = pos, current_pos_z * V_scale  # 현재 전주 측점 좌표
        next_pos_coord = next_pos, next_pos_z * V_scale  # 다음 전주 측점 좌표

        # offset 적용 좌표
        # h1 전차선
        # h2 조가선

        if current_airjoint:
            """에어조인트 각 구간별 브래킷 추가"""
            if current_airjoint == AirJoint.START.value:
                # 브래킷텍스트
                msp.add_mtext(f"{post_number}\n{pos}\n{bracket_type}\n{mast_name}",
                              dxfattribs={'insert': pos_coord, 'char_height': char_height, 'layer': '브래킷', 'color': 6})
                # 브래킷

                draw_bracket_at_profile(msp, pos_coord, current_structure)
            elif current_airjoint == AirJoint.POINT_2.value:
                # 브래킷 텍스트 추가
                msp.add_mtext(f"{post_number}\n{pos}\n'F(S),AJ-I\n{mast_name}",
                              dxfattribs={'insert': pos_coord, 'char_height': char_height, 'layer': '브래킷', 'color': 6})

                # 브래킷1 (좌측으로 0.5 이동)
                draw_bracket_at_profile(msp, (pos_coord[0] - 0.5, pos_coord[1]), current_structure)

                # 브래킷2 (우측으로 0.5 이동)
                draw_bracket_at_profile(msp, (pos_coord[0] + 0.5, pos_coord[1]), current_structure)

            elif current_airjoint == AirJoint.MIDDLE.value:
                # 브래킷텍스트
                msp.add_mtext(f"{post_number}\n{pos}\n'AJ-O,AJ-O\n{mast_name}",
                              dxfattribs={'insert': pos_coord, 'char_height': char_height, 'layer': '브래킷', 'color': 6})
                # 브래킷1 (좌측으로 0.5 이동)
                draw_bracket_at_profile(msp, (pos_coord[0] - 0.8, pos_coord[1]), current_structure)

                # 브래킷2 (우측으로 0.5 이동)
                draw_bracket_at_profile(msp, (pos_coord[0] + 0.8, pos_coord[1]), current_structure)
            elif current_airjoint == AirJoint.POINT_4.value:
                # 브래킷텍스트
                msp.add_mtext(f"{post_number}\n{pos}\n'AJ-O,F(L)\n{mast_name}",
                              dxfattribs={'insert': pos_coord, 'char_height': char_height, 'layer': '브래킷', 'color': 6})
                # 브래킷1 (좌측으로 0.5 이동)
                draw_bracket_at_profile(msp, (pos_coord[0] - 0.5, pos_coord[1]), current_structure)

                # 브래킷2 (우측으로 0.5 이동)
                draw_bracket_at_profile(msp, (pos_coord[0] + 0.5, pos_coord[1]), current_structure)
            elif current_airjoint == AirJoint.END.value:
                # 브래킷
                draw_bracket_at_profile(msp, pos_coord, current_structure)
                # 브래킷텍스트
                msp.add_mtext(f"{post_number}\n{pos}\n{bracket_type}\n{mast_name}",
                              dxfattribs={'insert': pos_coord, 'char_height': char_height, 'layer': '브래킷', 'color': 6})
            # 전주
            else:
                print('an error accumnent in line e')
        else:
            # 브래킷
            draw_bracket_at_profile(msp, pos_coord, current_structure)
            # 브래킷텍스트
            msp.add_mtext(f"{post_number}\n{pos}\n{bracket_type}\n{mast_name}",
                          dxfattribs={'insert': pos_coord, 'char_height': char_height, 'layer': '브래킷', 'color': 6})
        # 전주
        draw_mast_for_profile(msp, mast_name, pos_coord, current_structure)
    # 종단선형
    draw_profile_alignmnet(msp, polyline_with_sta)

    return doc, msp


def create_pegging_profile_wire(doc, msp, polyline, positions, structure_list, curve_list, pitchlist,
                                airjoint_list):
    post_number_lst = generate_postnumbers(positions)
    polyline_with_sta = [(i * 25, *values) for i, values in enumerate(polyline)]

    # 전주 데이터 구성
    pole_data = format_pole_data(DESIGNSPEED)

    char_height = 3 * H_scale
    for i in range(len(positions) - 1):
        pos, next_pos = positions[i], positions[i + 1]
        currentspan = next_pos - pos  # 현재 경간
        current_structure = isbridge_tunnel(pos, structure_list)  # 현재 구조물
        next_structure = isbridge_tunnel(next_pos, structure_list)  # 다음 구조물
        current_curve, R, c = iscurve(pos, curve_list)  # 현재 곡선
        current_slope, pitch = isslope(pos, pitchlist)  # 현재 구배
        current_airjoint = check_isairjoint(pos, airjoint_list)  # 현재 에어조인트
        current_pos_z = get_elevation_pos(pos, polyline_with_sta)  # 현재 전주의 z값
        next_pos_z = get_elevation_pos(next_pos, polyline_with_sta)  # 다음 전주의 z값
        post_number = find_post_number(post_number_lst, pos)  # 전주번호
        gauge = get_pole_gauge(DESIGNSPEED, current_structure)  # 구조물 offset
        _, mast_name = get_mast_type(DESIGNSPEED, current_structure)
        _, _, current_system_height, current_contact_height = get_contact_wire_and_massanger_wire_info(DESIGNSPEED,
                                                                                                       current_structure,
                                                                                                       currentspan)
        _, _, next_system_height, next_contact_height = get_contact_wire_and_massanger_wire_info(DESIGNSPEED,
                                                                                                 next_structure,
                                                                                                 currentspan)
        _, _, h1, h2, _, _ = initialrize_tenstion_device(pos, gauge, currentspan, current_contact_height,
                                                         current_system_height)
        h1 = h1 * V_scale
        h2 = h2 * V_scale

        # 스케일 적용된 높이
        # 스케일 적용된 높이 변환 (리스트 활용)
        current_system_height, current_contact_height, next_system_height, next_contact_height = [
            height * V_scale for height in
            (current_system_height, current_contact_height, next_system_height, next_contact_height)
        ]

        # 해당 구조물에 대한 전주 데이터 가져오기 (없으면 '토공' 기본값 사용)
        station_data = pole_data.get(current_structure, pole_data.get('토공', {}))

        # '교량' 같은 구간일 경우, 곡선 여부에 따라 데이터 선택
        if isinstance(station_data, dict) and '직선' in station_data:
            station_data = station_data.get('곡선' if current_curve == '곡선' else '직선', {})

        # 필요한 데이터 추출 (기본값 설정)
        I_type = station_data.get('I_type', '기본_I_type')
        O_type = station_data.get('O_type', '기본_O_type')
        I_bracket = station_data.get('I_bracket', '기본_I_bracket')
        O_bracket = station_data.get('O_bracket', '기본_O_bracket')

        # 홀수/짝수에 맞는 전주 데이터 생성
        pole_type = I_type if i % 2 == 1 else O_type
        bracket_type = I_bracket if i % 2 == 1 else O_bracket

        # 전주 좌표 반환
        pos_coord = pos, current_pos_z * V_scale  # 현재 전주 측점 좌표
        next_pos_coord = next_pos, next_pos_z * V_scale  # 다음 전주 측점 좌표

        # offset 적용 좌표
        # h1 전차선
        # h2 조가선

        if current_airjoint:
            """에어조인트 각 구간별 브래킷 추가"""
            if current_airjoint == AirJoint.START.value:

                # 무효선 좌표 계산
                y_offset = get_airjoint_xy(DESIGNSPEED, 'F형_시점')[1] * V_scale

                contact_start = (pos_coord[0], pos_coord[1] + h1)
                contact_end = (next_pos_coord[0], next_pos_coord[1] + next_contact_height + y_offset)

                massanger_start = (pos_coord[0], pos_coord[1] + h2)
                massanger_end = (next_pos_coord[0], next_pos_coord[1] + next_contact_height + next_system_height)

                # 무효선 그리기
                draw_msp_line(msp, contact_start, contact_end, layer_name='전차선', color=1)
                draw_msp_line(msp, massanger_start, massanger_end, layer_name='조가선', color=1)

                # 본선 그리기
                draw_contact_and_massanger_wire(msp, pos_coord, next_pos_coord, current_system_height,
                                                current_contact_height, next_system_height, next_contact_height)

            elif current_airjoint == AirJoint.POINT_2.value:
                # 무효선-하강
                # 무효선 좌표 계산
                y_offset = get_airjoint_xy(DESIGNSPEED, 'F형_시점')[1] * V_scale

                contact_start = (pos_coord[0], pos_coord[1] + current_contact_height + y_offset)
                contact_end = (next_pos_coord[0], next_pos_coord[1] + next_contact_height)

                massanger_start = (pos_coord[0], pos_coord[1] + current_contact_height + current_system_height)
                massanger_end = (next_pos_coord[0], next_pos_coord[1] + next_contact_height + next_system_height)

                # 무효선 그리기
                draw_msp_line(msp, contact_start, contact_end, layer_name='전차선', color=1)
                draw_msp_line(msp, massanger_start, massanger_end, layer_name='조가선', color=1)
                # 본선
                # 본선 그리기
                draw_contact_and_massanger_wire(msp, pos_coord, next_pos_coord, current_system_height,
                                                current_contact_height, next_system_height, next_contact_height)
            elif current_airjoint == AirJoint.MIDDLE.value:
                # 무효선 그리기
                draw_contact_and_massanger_wire(msp, pos_coord, next_pos_coord, current_system_height,
                                                current_contact_height, next_system_height, next_contact_height)

                y_offset = get_airjoint_xy(DESIGNSPEED, 'F형_시점')[1] * V_scale

                # 본선 상승
                contact_start = (pos_coord[0], pos_coord[1] + current_contact_height)
                contact_end = (next_pos_coord[0], next_pos_coord[1] + next_contact_height + y_offset)

                massanger_start = (pos_coord[0], pos_coord[1] + current_contact_height + current_system_height)
                massanger_end = (next_pos_coord[0], next_pos_coord[1] + next_contact_height + next_system_height)
                # 본선 그리기
                draw_msp_line(msp, contact_start, contact_end, layer_name='전차선', color=1)
                draw_msp_line(msp, massanger_start, massanger_end, layer_name='조가선', color=1)

            elif current_airjoint == AirJoint.POINT_4.value:
                y_offset = get_airjoint_xy(DESIGNSPEED, 'F형_시점')[1] * V_scale

                # 본선 상승
                contact_start = (pos_coord[0], pos_coord[1] + current_contact_height + y_offset)
                contact_end = (next_pos_coord[0], next_pos_coord[1] + h1)

                massanger_start = (pos_coord[0], pos_coord[1] + current_contact_height + current_system_height)
                massanger_end = (next_pos_coord[0], next_pos_coord[1] + h2)
                # 본선 그리기
                draw_msp_line(msp, contact_start, contact_end, layer_name='전차선', color=1)
                draw_msp_line(msp, massanger_start, massanger_end, layer_name='조가선', color=1)

                # 무효선
                draw_contact_and_massanger_wire(msp, pos_coord, next_pos_coord, current_system_height,
                                                current_contact_height, next_system_height, next_contact_height)
            else:
                # 본선
                draw_contact_and_massanger_wire(msp, pos_coord, next_pos_coord, current_system_height,
                                                current_contact_height, next_system_height, next_contact_height)
        else:
            # 전차선
            draw_contact_and_massanger_wire(msp, pos_coord, next_pos_coord, current_system_height,
                                            current_contact_height, next_system_height, next_contact_height)
        # 급전선
        draw_feeder_wire(msp, pos_coord, next_pos_coord, current_structure, next_structure)
        # 보호선
        draw_protect_wire(msp, pos_coord, next_pos_coord, current_structure, next_structure)

    return doc, msp


def get_airjoint_xy(DESIGNSPEED, content):
    return get_bracket_coordinates(DESIGNSPEED, content)


def draw_msp_line(msp, start_point, end_point, layer_name='0', color=0):
    msp.add_line(start_point, end_point, dxfattribs={'layer': layer_name, 'color': color})

    return msp


def draw_contact_and_massanger_wire(msp, start_pos, end_pos, system_height, contact_height, next_system_height,
                                    next_contact_height):
    """전차선 및 조가선 그리기"""
    # 전차선(컨택트 와이어) 시작과 끝 좌표 계산
    contact_wire_start_coord = (start_pos[0], start_pos[1] + contact_height)
    contact_wire_end_coord = (end_pos[0], end_pos[1] + next_contact_height)

    # 조가선(메신저 와이어) 시작과 끝 좌표 계산
    massanger_wire_start_coord = (contact_wire_start_coord[0], contact_wire_start_coord[1] + system_height)
    massanger_wire_end_coord = (contact_wire_end_coord[0], contact_wire_end_coord[1] + next_system_height)

    # Bulge 값 계산 (2H / L)
    chord_length = end_pos[0] - start_pos[0]  # 현의 길이
    sagitta = random.uniform(0, 0.5)  # 0 ~ 0.5 사이의 랜덤 Sagitta 값
    bulge = (2 * sagitta) / chord_length if chord_length != 0 else 0  # Bulge 값 계산

    # 전차선 추가
    msp.add_line(contact_wire_start_coord, contact_wire_end_coord, dxfattribs={'layer': '전차선', 'color': 3})

    # 조가선(메신저 와이어) 추가 (Bulge 적용)
    msp.add_lwpolyline(
        [(massanger_wire_start_coord[0], massanger_wire_start_coord[1], bulge),
         (massanger_wire_end_coord[0], massanger_wire_end_coord[1], 0)],
        format="xyb",  # x, y, bulge 형태로 추가
        close=False,
        dxfattribs={'layer': '조가선', 'color': 3}
    )

    return msp


def draw_feeder_wire(msp, start_pos, end_pos, current_structure, next_structure):
    """급전선(Feeder Wire) 그리기"""
    # 구조물별 급전선 높이 사전 정의
    feeder_wire_height_dict = {'토공': 7.23, '교량': 7.23, '터널': 5.48}

    # 현재 및 다음 구조물 높이 가져오기 (기본값: 토공)
    feeder_wire_start_height = feeder_wire_height_dict.get(current_structure, feeder_wire_height_dict['토공']) * V_scale
    feeder_wire_end_height = feeder_wire_height_dict.get(next_structure, feeder_wire_height_dict['토공']) * V_scale

    # 급전선 좌표 계산
    start_x, start_y = start_pos
    end_x, end_y = end_pos
    feeder_wire_start_coord = (start_x, start_y + feeder_wire_start_height)
    feeder_wire_end_coord = (end_x, end_y + feeder_wire_end_height)

    # Bulge 값 계산 (2H / L)
    chord_length = end_x - start_x  # 현의 길이
    sagitta = random.uniform(0, 0.8)  # 0 ~ 0.8 사이의 랜덤 Sagitta 값
    bulge = (2 * sagitta / chord_length) if chord_length != 0 else 0

    # DXF 폴리라인 추가
    msp.add_lwpolyline(
        [(start_x, feeder_wire_start_coord[1], bulge),
         (end_x, feeder_wire_end_coord[1], 0)],
        format="xyb",  # x, y, bulge 형태
        close=False,
        dxfattribs={'layer': '급전선', 'color': 2}
    )

    return msp


def draw_protect_wire(msp, start_pos, end_pos, current_structure, next_structure):
    # 보호선 높이 사전 정의
    wire_height_dict = {'토공': 4.887, '교량': 4.887, '터널': 5.56}

    # 구조물에 따른 보호선 높이 가져오기 (기본값 '토공')
    start_height = wire_height_dict.get(current_structure, wire_height_dict['토공']) * V_scale
    end_height = wire_height_dict.get(next_structure, wire_height_dict['토공']) * V_scale

    # 보호선 좌표 계산
    start_coord = (start_pos[0], start_pos[1] + start_height)
    end_coord = (end_pos[0], end_pos[1] + end_height)

    # Bulge 값 계산 (Sagitta 공식 적용)
    span_length = end_pos[0] - start_pos[0]
    sagitta = random.uniform(0, 0.8)  # 0~0.8 범위에서 랜덤 Sagitta 값
    bulge = 0 if span_length == 0 else (2 * sagitta) / span_length

    # 보호선 그리기
    msp.add_lwpolyline(
        [(start_coord[0], start_coord[1], bulge),
         (end_coord[0], end_coord[1], 0)],
        format="xyb",  # x, y, bulge 형태
        close=False,
        dxfattribs={'layer': '보호선', 'color': 11}
    )

    return msp


def draw_bracket_at_profile(msp, insert_point, current_structure):
    """가동 브래킷 종단면도 그리기"""
    # 파이프 치수 사전 정의
    tube_dimension_dict = {
        '토공': (6.3, 0.714, 0.386),
        '교량': (6.3, 0.714, 0.386),
        '터널': (5.748, 0.363, 0.386),
    }

    # 구조물에 따른 치수 가져오기 (기본값: 토공)
    top_tube_dim, main_pipe_dim, steady_arm_dim = tube_dimension_dict.get(
        current_structure, tube_dimension_dict['토공']
    )

    # 스케일 적용된 높이 계산
    top_tube_height = top_tube_dim * V_scale
    main_pipe_height = main_pipe_dim * V_scale
    steady_arm_height = steady_arm_dim * V_scale

    # 좌표 계산
    x, y = insert_point
    top_tube = (x, y + top_tube_height)
    main_pipe = (x, y + top_tube_height - main_pipe_height)
    steady_arm = (x, y + top_tube_height - main_pipe_height - steady_arm_height)

    # 브래킷 원 추가
    for position in [top_tube, main_pipe, steady_arm]:
        msp.add_circle(position, radius=0.03 * V_scale, dxfattribs={'layer': '브래킷', 'color': 6})

    return msp

def draw_profile_alignmnet(msp, polyline):
    # 폴리선 플롯
    polyline_x = [point[0] for point in polyline]
    polyline_y = [point[3] * V_scale for point in polyline]

    polyline_points = list(zip(polyline_x, polyline_y))  # 올바른 zip 사용
    msp.add_lwpolyline(polyline_points, close=False, dxfattribs={'layer': '종단선형', 'color': 1})

    return msp


def draw_mast_for_profile(msp, mast_name, mast_coord, current_structure):
    mast_length, mast_width = get_mast_length_and_width(mast_name)
    mast_length = mast_length * V_scale

    if current_structure in ['토공', '교량']:
        p1 = (mast_coord[0] + mast_width / 2, mast_coord[1])
    else:  # 터널
        p1 = (mast_coord[0] + mast_width / 2, mast_coord[1] + (4.54 * V_scale))

    p2 = p1[0], p1[1] + mast_length
    p3 = p2[0] - mast_width, p2[1]
    p4 = p3[0], p1[1]
    mast_points = [p1, p2, p3, p4]
    msp.add_lwpolyline(mast_points, close=True, dxfattribs={'layer': '전주', 'color': 4})

    return msp


def get_mast_length_and_width(mast_name: str):
    """딕셔너리를 활용해 전주 길이와 폭을 빠르게 추출하는 함수"""

    # 전주 길이 매핑
    mast_length_map = {
        'P-10"x7t-9m': 9,
        'P-12"x7t-8.5m': 8.5,
        '터널하수강': 1.735,
        'H형주-208X202': 9,
        'H형주-250X255': 10
    }

    # 전주 폭 매핑
    mast_width_map = {
        'P-10"x7t-9m': 0.2674,
        'P-12"x7t-8.5m': 0.312,
        '터널하수강': 0.25,
        'H형주-208X202': 0.25,
        'H형주-250X255': 0.25
        # H형주는 별도 규격이 없다고 가정
    }

    mast_length = mast_length_map.get(mast_name)
    mast_width = mast_width_map.get(mast_name)

    if mast_length is None or mast_width is None:
        raise ValueError(f"전주 정보 '{mast_name}'에서 길이 또는 폭을 찾을 수 없습니다.")

    return mast_length, mast_width


def return_pos_coord(polyline_with_sta, pos):
    point_a, P_A, vector_a = interpolate_coordinates(polyline_with_sta, pos)
    return point_a, vector_a


def save_to_dxf(doc, file_name='output.dxf'):
    doc.saveas(file_name)


def distribute_pole_spacing_flexible(start_km, end_km, spans=(45, 50, 55, 60)):
    """
    45, 50, 55, 60m 범위에서 전주 간격을 균형 있게 배분하여 전체 구간을 채우는 함수
    마지막 전주는 종점보다 약간 앞에 위치할 수도 있음.

    :param start_km: 시작점 (km 단위)
    :param end_km: 끝점 (km 단위)
    :param spans: 사용 가능한 전주 간격 리스트 (기본값: 45, 50, 55, 60)
    :return: 전주 간격 리스트, 전주 위치 리스트
    """
    start_m = int(start_km * 1000)  # km → m 변환
    end_m = int(end_km * 1000)

    positions = [start_m]
    selected_spans = []
    current_pos = start_m

    while current_pos < end_m:
        possible_spans = list(spans)  # 사용 가능한 간격 리스트 (45, 50, 55, 60)
        random.shuffle(possible_spans)  # 랜덤 배치

        for span in possible_spans:
            if current_pos + span > end_m:
                continue  # 종점을 넘어서면 다른 간격을 선택

            positions.append(current_pos + span)
            selected_spans.append(span)
            current_pos += span
            break  # 하나 선택하면 다음으로 이동

        # 더 이상 배치할 간격이 없으면 종료
        if current_pos + min(spans) > end_m:
            break

    return selected_spans, positions


# 전주번호 추가함수
def generate_postnumbers(lst):
    postnumbers = []
    prev_km = -1
    count = 0

    for number in lst:
        km = number // 1000  # 1000으로 나눈 몫이 같은 구간
        if km == prev_km:
            count += 1  # 같은 구간에서 숫자 증가
        else:
            prev_km = km
            count = 1  # 새로운 구간이므로 count를 0으로 초기화

        postnumbers.append((number, f'{km}-{count}'))

    return postnumbers


def find_structure_section(filepath):
    """xlsx 파일을 읽고 교량과 터널 정보를 반환하는 함수"""
    structure_list = {'bridge': [], 'tunnel': []}

    # xlsx 파일 읽기
    df_bridge = pd.read_excel(filepath, sheet_name='교량', header=None)
    df_tunnel = pd.read_excel(filepath, sheet_name='터널', header=None)

    # 교량 데이터 처리
    if df_bridge is not None and not df_bridge.empty:
        df_bridge.columns = ['br_NAME', 'br_START_STA', 'br_END_STA', 'br_LENGTH']
        for _, row in df_bridge.iterrows():
            structure_list['bridge'].append((row['br_START_STA'], row['br_END_STA']))
    else:
        # 빈 시트일 경우 기본 구조만 반환
        df_bridge = pd.DataFrame(columns=['br_NAME', 'br_START_STA', 'br_END_STA', 'br_LENGTH'])

    # 터널 데이터 처리
    if df_tunnel is not None and not df_tunnel.empty:
        df_tunnel.columns = ['tn_NAME', 'tn_START_STA', 'tn_END_STA', 'tn_LENGTH']
        for _, row in df_tunnel.iterrows():
            structure_list['tunnel'].append((row['tn_START_STA'], row['tn_END_STA']))
    else:
        # 빈 시트일 경우 기본 구조만 반환
        df_tunnel = pd.DataFrame(columns=['tn_NAME', 'tn_START_STA', 'tn_END_STA', 'tn_LENGTH'])

    return structure_list



def find_curve_section(txt_filepath='curveinfo.txt'):
    """txt 파일을 읽고 곧바로 측점(sta)과 곡선반경(radius) 정보를 반환하는 함수"""

    curve_list = []

    # 텍스트 파일(.txt) 읽기
    df_curve = pd.read_csv(txt_filepath, sep=",", header=None, names=['sta', 'radius', 'cant'])

    # 곡선 구간 정보 저장
    for _, row in df_curve.iterrows():
        curve_list.append((row['sta'], row['radius'], row['cant']))

    return curve_list


def find_pitch_section(txt_filepath='pitchinfo.txt'):
    """txt 파일을 읽고 곧바로 측점(sta)과 기울기(pitch) 정보를 반환하는 함수"""

    curve_list = []

    # 텍스트 파일(.txt) 읽기
    df_curve = pd.read_csv(txt_filepath, sep=",", header=None, names=['sta', 'radius'])

    # 곡선 구간 정보 저장
    for _, row in df_curve.iterrows():
        curve_list.append((row['sta'], row['radius']))

    return curve_list


def isbridge_tunnel(sta, structure_list):
    """sta가 교량/터널/토공 구간에 해당하는지 구분하는 함수"""
    for name, start, end in structure_list['bridge']:
        if start <= sta <= end:
            return '교량'

    for name, start, end in structure_list['tunnel']:
        if start <= sta <= end:
            return '터널'

    return '토공'


def iscurve(cur_sta, curve_list):
    """sta가 곡선 구간에 해당하는지 구분하는 함수"""
    rounded_sta = get_block_index(cur_sta)  # 25 단위로 반올림

    for sta, R, c in curve_list:
        if rounded_sta == sta:
            if R == 0:
                return '직선', 0, 0  # 반경이 0이면 직선
            return '곡선', R, c  # 반경이 존재하면 곡선

    return '직선', 0, 0  # 목록에 없으면 기본적으로 직선 처리


def isslope(cur_sta, curve_list):
    """sta가 곡선 구간에 해당하는지 구분하는 함수"""
    rounded_sta = get_block_index(cur_sta)  # 25 단위로 반올림

    for sta, g in curve_list:
        if rounded_sta == sta:
            if g == 0:
                return '수평', 0  # 반경이 0이면 직선
            else:
                return '기울기', f'{g * 1000:.2f}'

    return '수평', 0  # 목록에 없으면 기본적으로 직선 처리


def get_pole_data():
    """전주 데이터를 반환하는 기본 딕셔너리"""
    return {
        150: {
            'prefix': 'Cako150',
            'tunnel': (947, 946),
            'earthwork': (544, 545),
            'straight_bridge': (556, 557),
            'curve_bridge': (562, 563),
        },
        250: {
            'prefix': 'Cako250',
            'tunnel': (979, 977),  # 터널은 I,O반대
            'earthwork': (508, 510),
            'straight_bridge': (512, 514),
            'curve_bridge': (527, 529),
        },
        350: {
            'prefix': 'Cako350',
            'tunnel': (569, 568),
            'earthwork': (564, 565),
            'straight_bridge': (566, 567),
            'curve_bridge': (566, 567),
        }
    }


def format_pole_data(design_speed):
    """설계 속도에 따른 전주 데이터를 특정 형식으로 변환"""
    base_data = get_pole_data()

    if design_speed not in base_data:
        raise ValueError("올바른 DESIGNSPEED 값을 입력하세요 (150, 250, 350)")

    data = base_data[design_speed]
    prefix = data['prefix']

    def create_pole_types(i_type, o_type, bracket_suffix):
        return {
            'I_type': i_type,
            'O_type': o_type,
            'I_bracket': f'{prefix}_{bracket_suffix}-I',
            'O_bracket': f'{prefix}_{bracket_suffix}-O',
        }

    return {
        '교량': {
            '직선': create_pole_types(*data['straight_bridge'], 'OpG3.5'),
            '곡선': create_pole_types(*data['curve_bridge'], 'OpG3.5'),
        },
        '터널': create_pole_types(*data['tunnel'], 'Tn'),
        '토공': create_pole_types(*data['earthwork'], 'OpG3.0'),
    }


def define_airjoint_section(positions):
    airjoint_list = []  # 결과 리스트
    airjoint_span = 1600  # 에어조인트 설치 간격(m)

    def is_near_multiple_of_DIG(number, tolerance=100):
        """주어진 수가 1200의 배수에 근사하는지 판별하는 함수"""
        remainder = number % airjoint_span
        return number > airjoint_span and (remainder <= tolerance or remainder >= (airjoint_span - tolerance))

    i = 0  # 인덱스 변수
    while i < len(positions) - 1:  # 마지막 전주는 제외
        pos = positions[i]  # 현재 전주 위치

        if is_near_multiple_of_DIG(pos):  # 조건 충족 시
            next_values = positions[i + 1:min(i + 6, len(positions))]  # 다음 5개 값 가져오기
            tags = [
                AirJoint.START.value,
                AirJoint.POINT_2.value,
                AirJoint.MIDDLE.value,
                AirJoint.POINT_4.value,
                AirJoint.END.value
            ]

            # (전주 위치, 태그) 쌍을 리스트에 추가 (최대 5개까지만)
            airjoint_list.extend(list(zip(next_values, tags[:len(next_values)])))

            # 다음 5개의 값을 가져왔으므로 인덱스를 건너뛰기
            i += 5
        else:
            i += 1  # 조건이 맞지 않으면 한 칸씩 이동

    return airjoint_list


def check_isairjoint(input_sta, airjoint_list):
    for data in airjoint_list:
        sta, tag = data
        if input_sta == sta:
            return tag


def write_to_file(filename, lines):
    """리스트 데이터를 파일에 저장하는 함수"""
    try:
        # 디렉토리 자동 생성
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, "w", encoding="utf-8") as f:
            f.writelines(lines)  # 리스트 데이터를 한 번에 파일에 작성

        print(f"✅ 파일 저장 완료: {filename}")
    except Exception as e:
        print(f"⚠️ 파일 저장 중 오류 발생: {e}")


def get_airjoint_bracket_data():
    """에어조인트 브래킷 데이터를 반환하는 기본 딕셔너리"""
    return {
        150: {
            'prefix': 'Cako150',  # 150급은 별도의 aj없음
            '터널': (941, 942),  # G2.1 I,0
            '토공': (1252, 1253),  # G3.0 I,O
            '교량': (1254, 1255),  # G3.5 I,O
        },
        250: {
            'prefix': 'Cako250',
            '터널': (1325, 1326),  # CAKO250-Tn-AJ
            '토공': (1296, 1297),  # CAKO250-G3.0-AJ
            '교량': (1298, 1299),  # CAKO250-G3.5-AJ
        },
        350: {
            'prefix': 'Cako350',
            '터널': (639, 640),  # CAKO350-Tn-AJ
            '토공': (635, 636),  # CAKO350-G3.0-AJ
            '교량': (637, 638),  # CAKO350-G3.5-AJ
        }
    }


def get_F_bracket_data():
    """F브래킷 데이터를 반환하는 기본 딕셔너리"""
    return {
        150: {
            'prefix': 'Cako150',
            '터널': (1330, 1330),  # TN-F
            '토공': (1253, 1253),  # G3.0F
            '교량': (1255, 1255),  # G3.5-F
        },
        250: {
            'prefix': 'Cako250',
            '터널': (1290, 1291),
            '토공': (1284, 1285),  # CAKO250-G3.0-F(S) CAKO250-G3.0-F(L)
            '교량': (1286, 1287),  # CAKO250-G3.5-F
        },
        350: {
            'prefix': 'Cako350',
            '터널': (582, 583),  # CAKO350-Tn-F
            '토공': (578, 579),  # CAKO350-G3.0-F(S) CAKO250-G3.0-F(L)
            '교량': (580, 581),  # CAKO350-G3.5-F
        }
    }


def get_airjoint_fitting_data():
    """에어조인트 브래킷 금구류 데이터를 반환하는 기본 딕셔너리"""
    return {
        150: {
            'prefix': 'Cako150',
            '에어조인트': 499,  # 에어조인트용 조가선 지지금구
            'FLAT': (1292, 1292),  # 무효인상용 조가선,전차선 지지금구(150-급에서는 f형 돼지꼬리)
            '곡선당김금구': (1293, 1294),  # L,R
        },
        250: {
            'prefix': 'Cako250',  #
            '에어조인트': 1279,  # 에어조인트용 조가선 지지금구
            'FLAT': (1281, 1282),  # 무효인상용 조가선, 전차선  지지금구
            '곡선당김금구': (1280, 1283)  # L,R
        },
        350: {
            'prefix': 'Cako350',  # 350
            '에어조인트': 586,  # 에어조인트용 조가선 지지금구
            'FLAT': (584, 585),  # 무효인상용 조가선, 전차선  지지금구
            '곡선당김금구': (576, 577),  # L,R
        }
    }


def get_airjoint_lines(pos, next_pos, current_airjoint, pole_type, bracket_type, current_structure, next_structure,
                       DESIGNSPEED, currentspan, polyline_with_sta):
    """에어조인트 구간별 전주 데이터 생성"""
    lines = []

    # 데이터 가져오기
    airjoint_fitting, flat_fitting, steady_arm_fitting, mast_type, mast_name, offset = get_fitting_and_mast_data(
        DESIGNSPEED, current_structure, bracket_type)
    bracket_values, f_values = get_bracket_codes(DESIGNSPEED, current_structure)

    # 구조물별 건식게이지 값
    gauge = get_pole_gauge(DESIGNSPEED, current_structure)
    next_gauge = get_pole_gauge(DESIGNSPEED, next_structure)
    # 에어조인트 각도 가져오기
    stagger, y1 = get_bracket_coordinates(DESIGNSPEED, 'F형_끝')

    bracket_code_start, bracket_code_end = bracket_values
    f_code_start, f_code_end = f_values

    # 전주 추가
    add_pole(lines, pos, current_airjoint, pole_type, bracket_type)

    # 급전선 설비 인덱스 가져오기
    feeder_idx = get_feeder_insulator_idx(DESIGNSPEED, current_structure)

    # 평행틀 설비 인덱스 가져오기
    spreader_name, spreader_idx = get_spreader_idx(DESIGNSPEED, current_structure, current_airjoint)

    # 공통 텍스트(전주,급전선,평행틀
    if current_airjoint in [AirJoint.POINT_2.value, AirJoint.MIDDLE.value, AirJoint.POINT_4.value]:
        common_lines(lines, mast_type, offset, mast_name, feeder_idx, spreader_name, spreader_idx)

    # 모든 필요한 값들을 딕셔너리로 묶어서 전달
    params = {
        'polyline_with_sta': polyline_with_sta,
        'current_airjoint': current_airjoint,
        'lines': lines,
        'pos': pos,
        'next_pos': next_pos,
        'DESIGNSPEED': DESIGNSPEED,
        'airjoint_fitting': airjoint_fitting,
        'steady_arm_fitting': steady_arm_fitting,
        'flat_fitting': flat_fitting,
        'pole_type': pole_type,
        'bracket_type': bracket_type,
        'offset': offset,
        'f_code_start': f_code_start,
        'f_code_end': f_code_end,
        'bracket_code_start': bracket_code_start,
        'bracket_code_end': bracket_code_end,
        'current_structure': current_structure,
        'next_structure': next_structure,
        'gauge': gauge,
        'next_gauge': next_gauge
    }
    # 에어조인트 구간별 처리(2호주 ,3호주, 4호주)
    add_airjoint_brackets(params)

    return lines


def add_airjoint_brackets(params):
    # 인자 분해
    """에어조인트 각 구간별 브래킷 추가"""
    polyline_with_sta = params['polyline_with_sta']
    current_airjoint = params['current_airjoint']
    lines = params['lines']
    pos = params['pos']
    next_pos = params['next_pos']
    DESIGNSPEED = params['DESIGNSPEED']
    airjoint_fitting = params['airjoint_fitting']
    steady_arm_fitting = params['steady_arm_fitting']
    flat_fitting = params['flat_fitting']
    pole_type = params['pole_type']
    bracket_type = params['bracket_type']
    offset = params['offset']
    f_code_start = params['f_code_start']
    f_code_end = params['f_code_end']
    bracket_code_start = params['bracket_code_start']
    bracket_code_end = params['bracket_code_end']
    current_structure = params['current_structure']
    next_structure = params['next_structure']
    gauge = params['gauge']
    next_gauge = params['next_gauge']

    x, y = get_bracket_coordinates(DESIGNSPEED, 'AJ형_시점')
    x1, y1 = get_bracket_coordinates(DESIGNSPEED, 'F형_시점')
    x2, y2 = get_bracket_coordinates(DESIGNSPEED, 'AJ형_중간1')
    x3, y3 = get_bracket_coordinates(DESIGNSPEED, 'AJ형_중간2')
    x4, y4 = get_bracket_coordinates(DESIGNSPEED, 'AJ형_끝')
    x5, y5 = get_bracket_coordinates(DESIGNSPEED, 'F형_끝')

    """에어조인트 각 구간별 브래킷 추가"""
    if current_airjoint == AirJoint.START.value:
        # START 구간 처리
        start_angle = calculate_curve_angle(polyline_with_sta, pos, next_pos, gauge, x1)
        lines.extend([
            f".freeobj 0;{pole_type};,;{bracket_type}\n",
            f".freeobj 0;1247;{offset};0;{start_angle},;스프링식 장력조절장치\n"
        ])

    elif current_airjoint == AirJoint.POINT_2.value:
        # POINT_2 구간 처리
        add_F_and_AJ_brackets(DESIGNSPEED, lines, pos, f_code_start, bracket_code_start, airjoint_fitting,
                              steady_arm_fitting, flat_fitting)

    elif current_airjoint == AirJoint.MIDDLE.value:
        # MIDDLE 구간 처리
        add_AJ_brackets_middle(DESIGNSPEED, lines, pos, bracket_code_start, bracket_code_end, airjoint_fitting,
                               steady_arm_fitting)

    elif current_airjoint == AirJoint.POINT_4.value:
        # POINT_4 구간 처리
        add_F_and_AJ_brackets(DESIGNSPEED, lines, pos, f_code_end, bracket_code_end, airjoint_fitting,
                              steady_arm_fitting, flat_fitting, end=True)

    elif current_airjoint == AirJoint.END.value:
        # END 구간 처리
        end_angle = calculate_curve_angle(polyline_with_sta, pos, next_pos, x5, next_gauge)
        lines.append(f".freeobj 0;{pole_type};,;{bracket_type}\n")
        lines.append(f".freeobj 0;1247;{offset};0;{180 + end_angle};,;스프링식 장력조절장치\n")


def add_F_and_AJ_brackets(DESIGNSPEED, lines, pos, f_code, bracket_code, airjoint_fitting, steady_arm_fitting,
                          flat_fitting, end=False):
    """F형 및 AJ형 브래킷을 추가하는 공통 함수"""
    # F형 가동 브래킷 추가
    x1, y1 = get_bracket_coordinates(DESIGNSPEED, 'F형_시점' if not end else 'F형_끝')
    add_F_bracket(DESIGNSPEED, lines, pos - 0.528, f_code, "가동브래킷 F형", flat_fitting, x1, y1)

    # AJ형 가동 브래킷 추가
    x1, y1 = get_bracket_coordinates(DESIGNSPEED, 'AJ형_시점' if not end else 'AJ형_끝')
    add_AJ_bracket(lines, pos + 0.528, bracket_code, '가동브래킷 AJ형', airjoint_fitting,
                   steady_arm_fitting[0] if not end else steady_arm_fitting[1], x1, y1)


def add_AJ_brackets_middle(DESIGNSPEED, lines, pos, bracket_code_start, bracket_code_end, airjoint_fitting,
                           steady_arm_fitting):
    """MIDDLE 구간에서 AJ형 브래킷 추가"""
    # AJ형 가동 브래킷 및 금구류 추가
    x1, y1 = get_bracket_coordinates(DESIGNSPEED, 'AJ형_중간1')
    bracket_code_else = bracket_code_start if DESIGNSPEED == 150 else bracket_code_end
    steady_arm_fitting_else = steady_arm_fitting[0] if DESIGNSPEED == 150 else steady_arm_fitting[1]
    add_AJ_bracket(lines, pos - 0.8, bracket_code_else, '가동브래킷 AJ형', airjoint_fitting, steady_arm_fitting_else, x1, y1)

    # AJ형 가동 브래킷 및 금구류 추가
    x1, y1 = get_bracket_coordinates(DESIGNSPEED, 'AJ형_중간2')
    add_AJ_bracket(lines, pos + 0.8, bracket_code_end, '가동브래킷 AJ형', airjoint_fitting, steady_arm_fitting[1], x1, y1)


def get_fitting_and_mast_data(DESIGNSPEED, current_structure, bracket_type):
    """금구류 및 전주 데이터를 가져옴"""
    fitting_data = get_airjoint_fitting_data().get(DESIGNSPEED, {})
    airjoint_fitting = fitting_data.get('에어조인트', 0)
    flat_fitting = fitting_data.get('FLAT', (0, 0))
    steady_arm_fitting = fitting_data.get('곡선당김금구', (0, 0))

    mast_type, mast_name = get_mast_type(DESIGNSPEED, current_structure)

    offset = get_pole_gauge(DESIGNSPEED, current_structure)

    return airjoint_fitting, flat_fitting, steady_arm_fitting, mast_type, mast_name, offset


def get_mast_type(DESIGNSPEED, current_structure):
    # 전주 인덱스 딕셔너리(idx,comment)
    mast_dic = {
        150: {
            'prefix': 'Cako150',
            '토공': (1370, 'P-10"x7t-9m'),
            '교량': (1376, 'P-12"x7t-8.5m'),
            '터널': (1400, '터널하수강'),
        },
        250: {
            'prefix': 'Cako250',
            '토공': (1370, 'P-10"x7t-9m'),
            '교량': (1376, 'P-12"x7t-8.5m'),
            '터널': (1400, '터널하수강'),
        },
        350: {
            'prefix': 'Cako350',  # 350
            '토공': (619, 'H형주-208X202'),
            '교량': (620, 'H형주-250X255'),
            '터널': (621, '터널하수강'),
        }
    }
    mast_data = mast_dic.get(DESIGNSPEED, mast_dic[250])
    mast_type, mast_name = mast_data.get(current_structure, ("", "알 수 없는 구조"))

    return mast_type, mast_name


def get_bracket_codes(DESIGNSPEED, current_structure):
    """브래킷 코드 가져오기"""
    airjoint_data = get_airjoint_bracket_data().get(DESIGNSPEED, {})
    f_data = get_F_bracket_data().get(DESIGNSPEED, {})

    bracket_values = airjoint_data.get(current_structure, (0, 0))
    f_values = f_data.get(current_structure, (0, 0))

    return bracket_values, f_values


def add_pole(lines, pos, current_airjoint, pole_type, bracket_type):
    """전주를 추가하는 함수"""
    lines.extend([
        f"\n,;-----{current_airjoint}-----\n",
        f"{pos}\n"
    ])


# 에어조인트 편위와 인상높이 딕셔너리
def get_bracket_coordinates(DESIGNSPEED, bracket_type):
    """설계속도와 브래킷 유형에 따른 좌표 반환"""
    coordinates = {
        "F형_시점": {
            150: (-0.35, 0.3),
            250: (-0.3, 0.32),
            350: (-0.7, 0.5)
        },
        "AJ형_시점": {
            150: (-0.15, 0),
            250: (-0.1, 0),
            350: (-0.2, 0)
        },
        "AJ형_중간1": {
            150: (-0.15, 0),
            250: (-0.1, 0),
            350: (-0.25, 0)
        },
        "AJ형_중간2": {
            150: (0.15, 0),
            250: (0.1, 0),
            350: (0.25, 0)
        },
        "AJ형_끝": {
            150: (0.15, 0),
            250: (0.1, 0),
            350: (0.2, 0)
        },
        "F형_끝": {
            150: (0.35, 0.3),
            250: (0.3, 0.32),
            350: (0.7, 0.5)
        },
    }

    # 지정된 브래킷 유형과 속도에 맞는 좌표 반환
    return coordinates.get(bracket_type, {}).get(DESIGNSPEED, (0, 0))


def common_lines(lines, mast_type, offset, mast_name, feeder_idx, spreader_name, spreader_idx):
    lines.extend([
        ',;전주 구문\n',
        f".freeobj 0;{mast_type};{offset};,;{mast_name}\n",
        f".freeobj 0;{feeder_idx};{offset};,;급전선 현수 조립체\n",
        f".freeobj 0;{spreader_idx};{offset};,;{spreader_name}\n\n"
    ])


def get_feeder_insulator_idx(DESIGNSPEED, current_structure):
    idx_dic = {
        150: {
            'prefix': 'Cako150',
            '토공': 1234,
            '교량': 1234,
            '터널': 1249
        },
        250: {
            'prefix': 'Cako250',
            '토공': 1234,
            '교량': 1234,
            '터널': 1249
        },
        350: {
            'prefix': 'Cako350',
            '토공': 597,
            '교량': 597,
            '터널': 598
        }
    }

    idx_data = idx_dic.get(DESIGNSPEED, idx_dic[250])
    idx = idx_data.get(current_structure, idx_data['토공'])
    return idx


def get_spreader_idx(DESIGNSPEED, current_structure, current_airjoint):
    """평행틀 인덱스를 반환하는 기본 딕셔너리"""
    spreader_dictionary = {
        150: {
            'prefix': 'Cako150',
            '토공': (531, 532),
            '교량': (534, 535),
            '터널': (537, 538)
        },
        250: {
            'prefix': 'Cako250',
            '토공': (531, 532),
            '교량': (534, 535),
            '터널': (537, 538)
        },
        350: {
            'prefix': 'Cako350',
            '토공': (587, 588),
            '교량': (589, 590),
            '터널': (587, 588)
        }
    }

    spreader_data = spreader_dictionary.get(DESIGNSPEED, spreader_dictionary[250])
    spreader_str = spreader_data.get(current_structure, (0, 0))  # 기본값 (0, 0) 설정

    if current_airjoint in ['에어조인트 2호주', '에어조인트 4호주']:
        spreader_idx = spreader_str[0]
        spreader_name = '평행틀-1m'
    elif current_airjoint in ['에어조인트 중간주 (3호주)']:
        spreader_idx = spreader_str[1]
        spreader_name = '평행틀-1.6m'
    else:
        spreader_idx = spreader_str[0]
        spreader_name = '평행틀-1m'

    return spreader_name, spreader_idx


def add_F_bracket(DESIGNSPEED, lines, pos, bracket_code, bracket_type, fitting_data, x1, y1):
    """F형 가동 브래킷 및 금구류 추가"""
    idx1, idx2 = fitting_data
    if DESIGNSPEED == 150:
        lines.extend([
            ',;가동브래킷구문\n',
            f"{pos},.freeobj 0;{bracket_code};0;{y1};,;{bracket_type}\n",
            f"{pos},.freeobj 0;{idx1};{x1};{y1},;조가선지지금구-F용\n",
            f"{pos},.freeobj 0;{idx2};{x1};{y1},;전차선선지지금구-F용\n",
        ])
    else:
        lines.extend([
            ',;가동브래킷구문\n',
            f"{pos},.freeobj 0;{bracket_code};0;0;,;{bracket_type}\n",
            f"{pos},.freeobj 0;{idx1};{x1};0,;조가선지지금구-F용\n",
            f"{pos},.freeobj 0;{idx2};{x1};0,;전차선선지지금구-F용\n",
        ])


def add_AJ_bracket(lines, pos, bracket_code, bracket_type, fitting_data, steady_arm_fitting, x1, y1):
    """AJ형 가동 브래킷 및 금구류 추가"""
    lines.extend([
        ',;가동브래킷구문\n',
        f"{pos},.freeobj 0;{bracket_code};0;0;,;{bracket_type}\n",
        f"{pos},.freeobj 0;{fitting_data};{x1};{y1},;조가선지지금구-AJ용\n",
        f"{pos},.freeobj 0;{steady_arm_fitting};{x1};{y1},;곡선당김금구\n",
    ])


def find_post_number(lst, pos):
    for arg in lst:
        if arg[0] == pos:
            return arg[1]


def save_to_txt(positions, structure_list, curve_list, pitchlist, DESIGNSPEED, airjoint_list, polyline,
                filename="C:/TEMP/pole_positions.txt"):
    """전주 위치 데이터를 가공하여 .txt 파일로 저장하는 함수"""
    polyline_with_sta = [(i * 25, *values) for i, values in enumerate(polyline)]
    # 전주 데이터 구성
    pole_data = format_pole_data(DESIGNSPEED)

    lines = []  # 파일에 저장할 데이터를 담을 리스트
    # 전주번호
    post_number_lst = generate_postnumbers(positions)

    for i in range(len(positions) - 1):
        pos, next_pos = positions[i], positions[i + 1]
        currentspan = next_pos - pos  # 전주 간 거리 계산
        # 현재 위치의 구조물 및 곡선 정보 가져오기
        current_structure = isbridge_tunnel(pos, structure_list)
        next_structure = isbridge_tunnel(next_pos, structure_list)
        current_curve, R, c = iscurve(pos, curve_list)
        current_slope, pitch = isslope(pos, pitchlist)
        current_airjoint = check_isairjoint(pos, airjoint_list)
        post_number = find_post_number(post_number_lst, pos)
        # 해당 구조물에 대한 전주 데이터 가져오기 (없으면 '토공' 기본값 사용)
        station_data = pole_data.get(current_structure, pole_data.get('토공', {}))

        # '교량' 같은 구간일 경우, 곡선 여부에 따라 데이터 선택
        if isinstance(station_data, dict) and '직선' in station_data:
            station_data = station_data.get('곡선' if current_curve == '곡선' else '직선', {})

        # 필요한 데이터 추출 (기본값 설정)
        I_type = station_data.get('I_type', '기본_I_type')
        O_type = station_data.get('O_type', '기본_O_type')
        I_bracket = station_data.get('I_bracket', '기본_I_bracket')
        O_bracket = station_data.get('O_bracket', '기본_O_bracket')

        # 홀수/짝수에 맞는 전주 데이터 생성
        pole_type = I_type if i % 2 == 1 else O_type
        bracket_type = I_bracket if i % 2 == 1 else O_bracket

        if current_airjoint:
            lines.extend(f'\n,;{post_number}')
            lines.extend(get_airjoint_lines(pos, next_pos, current_airjoint, pole_type, bracket_type, current_structure,
                                            next_structure, DESIGNSPEED, currentspan, polyline_with_sta))
        else:
            lines.append(f'\n,;{post_number}')
            lines.append(f'\n,;-----일반개소({current_structure})({current_curve})-----\n')
            lines.append(f"{pos},.freeobj 0;{pole_type};,;{bracket_type}\n")

    # 파일 저장 함수 호출
    write_to_file(filename, lines)

def open_excel_file():
    """파일 선택 대화 상자를 열고, 엑셀 파일 경로를 반환하는 함수"""
    root = tk.Tk()
    root.withdraw()  # Tkinter 창을 숨김
    file_path = filedialog.askopenfilename(
        title="엑셀 파일 선택",
        filetypes=[("Excel Files", "*.xlsx")]
    )

    return file_path


def get_block_index(current_track_position, block_interval=25):
    """현재 트랙 위치를 블록 인덱스로 변환"""
    return math.floor(current_track_position / block_interval + 0.001) * block_interval


def process_to_WIRE(DESIGNSPEED, positions, spans, structure_list, curve_list, pitchlist, polyline, airjoint_list,
                    filename="wire.txt"):
    """ 전주 위치에 wire를 배치하는 함수 """
    post_number_lst = generate_postnumbers(positions)
    polyline_with_sta = [(i * 25, *values) for i, values in enumerate(polyline)]
    lines = []
    for i in range(len(positions) - 1):
        pos, next_pos = positions[i], positions[i + 1]
        currentspan = next_pos - pos  # 전주 간 거리 계산
        current_structure = isbridge_tunnel(pos, structure_list)
        next_structure = isbridge_tunnel(next_pos, structure_list)
        current_curve, R, c = iscurve(pos, curve_list)
        current_slope, pitch = isslope(pos, pitchlist)  # 현재 측점의 구배
        next_slope, next_pitch = isslope(next_pos, pitchlist)  # 다음 측점의 구배
        current_z = get_elevation_pos(pos, polyline_with_sta)  # 현재 측점의 z값
        next_z = get_elevation_pos(next_pos, polyline_with_sta)  # 다음 측점의 z값
        # z값 param
        param_z = {
            'current_slope': current_slope,
            'pitch': pitch,
            'next_slope': next_slope,
            'next_pitch': next_pitch,
            'current_z': current_z,
            'next_z': next_z
        }

        current_sta = get_block_index(pos)
        current_airjoint = check_isairjoint(pos, airjoint_list)
        currnet_type = 'I' if i % 2 == 1 else 'O'
        post_number = find_post_number(post_number_lst, pos)
        obj_index, comment, AF_wire, FPW_wire = get_wire_span_data(DESIGNSPEED, currentspan, current_structure)

        # AF와 FPW오프셋(X,Y)
        AF_X_offset, AF_y_offset, fpw_wire_X_offset, fpw_wire_y_offset = get_wire_offsetanlge(DESIGNSPEED,
                                                                                              current_structure)
        # 다음
        AF_X_offset_Next, AF_y_offset_Next, fpw_wire_X_offset_Next, fpw_wire_y_offset_Next = get_wire_offsetanlge(
            DESIGNSPEED, next_structure)

        # 편위(0.2)와 직선구간 각도
        lateral_offset, adjusted_angle = get_lateral_offset_and_angle(i, currentspan)

        lines.extend([f'\n,;{post_number}'])
        if current_airjoint in ['에어조인트 시작점 (1호주)', '에어조인트 (2호주)', '에어조인트 중간주 (3호주)', '에어조인트 (4호주)', '에어조인트 끝점 (5호주)']:
            lines.extend([f'\n,;-----{current_airjoint}({current_structure})-----\n'])
        else:

            lines.extend([f'\n,;-----일반개소({current_structure})({current_curve})-----\n'])

        lines.extend(handle_curve_and_straight_section(pos, next_pos, currentspan, polyline_with_sta, current_airjoint,
                                                       obj_index, comment, currnet_type, current_structure,
                                                       next_structure, param_z, DESIGNSPEED))
        adjusted_angle = calculate_curve_angle(polyline_with_sta, pos, next_pos, AF_X_offset, AF_X_offset_Next)
        pitch_angle = change_permile_to_degree(pitch)
        topdown_angle = calculate_slope(current_z + AF_y_offset, next_z + AF_y_offset_Next, currentspan) - pitch_angle  # 전차선 상하각도
        lines.append(f"{pos},.freeobj 0;{AF_wire};{AF_X_offset};{AF_y_offset};{adjusted_angle};{topdown_angle};,;급전선\n")
        adjusted_angle = calculate_curve_angle(polyline_with_sta, pos, next_pos, fpw_wire_X_offset,
                                               fpw_wire_X_offset_Next)
        topdown_angle = calculate_slope(current_z + fpw_wire_y_offset, next_z + fpw_wire_y_offset_Next, currentspan) - pitch_angle
        lines.append(
            f"{pos},.freeobj 0;{FPW_wire};{fpw_wire_X_offset};{fpw_wire_y_offset};{adjusted_angle};{topdown_angle};,;FPW\n")

    buffered_write(filename, lines)


def get_elevation_pos(pos, polyline_with_sta):
    new_z = None

    for i in range(len(polyline_with_sta) - 1):
        sta1, x1, y1, z1 = polyline_with_sta[i]  # 현재값
        sta2, x2, y2, z2 = polyline_with_sta[i + 1]  # 다음값
        L = sta2 - sta1
        L_new = pos - sta1

        if sta1 <= pos < sta2:
            new_z = calculate_height_at_new_distance(z1, z2, L, L_new)
            return new_z

    return new_z


def calculate_height_at_new_distance(h1, h2, L, L_new):
    """주어진 거리 L에서의 높이 변화율을 기반으로 새로운 거리 L_new에서의 높이를 계산"""
    h3 = h1 + ((h2 - h1) / L) * L_new
    return h3

def get_wire_offsetanlge(DESIGNSPEED, current_structure):
    """AF,FPW offset을 반환하는 기본 딕셔너리(x,y)"""
    AF_offset_values = {
        150: {
            'prefix': 'Cako150',
            '토공': (-1.637, 7.228381),
            '교량': (-2.137, 7.228381),
            '터널': (-1.919, 5.479)
        },
        250: {
            'prefix': 'Cako250',
            '토공': (-1.637, 7.228381),
            '교량': (-2.137, 7.228381),
            '터널': (-1.919, 5.479)
        },
        350: {
            'prefix': 'Cako350',
            '토공': (-4.356,  6.154),
            '교량': (-2.419, 8.133),
            '터널': (1.598, 8.067)
        }
    }

    FPW_offset_values = {
        150: {
            'prefix': 'Cako150',
            '토공': (-3.239, 4.89),
            '교량': (-3.7397,4.89),
            '터널': (2.049, 5.559)
        },
        250: {
            'prefix': 'Cako250',
            '토공': (-3.239,  4.89),
            '교량': (-3.7397, 4.89),
            '터널': (2.049, 5.559)
        },
        350: {
            'prefix': 'Cako350',
            '토공': (-3.42, 5.505),
            '교량': (-3.671, 5.505),
            '터널': (2.206,7.766)
        }
    }
    AF_data = AF_offset_values.get(DESIGNSPEED, AF_offset_values[250])
    AF_X_offset, AF_y_offset = AF_data[current_structure]
    FPW_data = FPW_offset_values.get(DESIGNSPEED, FPW_offset_values[250])
    fpw_wire_X_offset, fpw_wire_y_offset = FPW_data[current_structure]

    return [AF_X_offset, AF_y_offset, fpw_wire_X_offset, fpw_wire_y_offset]


def buffered_write(filename, lines):
    """파일 쓰기 버퍼 함수"""
    with open(filename, "w", encoding="utf-8") as f:
        f.writelines(lines)


def get_wire_span_data(DESIGNSPEED, currentspan, current_structure):
    """ 경간에 따른 wire 데이터 반환 """
    # SPEED STRUCTURE span 45, 50, 55, 60
    span_data = {
        150: {
            'prefix': 'Cako150',
            '토공': (592, 593, 594, 595),  # 가고 960
            '교량': (592, 593, 594, 595),  # 가고 960
            '터널': (614, 615, 616, 617)  # 가고 710
        },
        250: {
            'prefix': 'Cako250',
            '토공': (484, 478, 485, 479),  # 가고 1200
            '교량': (484, 478, 485, 479),  # 가고 1200
            '터널': (494, 495, 496, 497)  # 가고 850
        },
        350: {
            'prefix': 'Cako350',
            '토공': (488, 489, 490, 491),  # 가고 1400
            '교량': (488, 489, 490, 491),  # 가고 1400
            '터널': (488, 489, 490, 491)  # 가고 1400
        }
    }

    # DESIGNSPEED에 맞는 구조 선택 (기본값 250 사용)
    span_values = span_data.get(DESIGNSPEED, span_data[250])

    # current_structure에 맞는 값 추출
    current_structure_list = span_values[current_structure]

    # currentspan 값을 통해 인덱스를 추출
    span_index_mapping = {
        45: (0, '경간 45m', 1236, 1241),
        50: (1, '경간 50m', 1237, 1242),
        55: (2, '경간 55m', 1238, 1243),
        60: (3, '경간 60m', 1239, 1244)
    }

    # currentspan이 유효한 값인지 확인
    if currentspan not in span_index_mapping:
        raise ValueError(f"Invalid span value '{currentspan}'. Valid values are 45, 50, 55, 60.")

    # currentspan에 해당하는 인덱스 및 주석 추출
    idx, comment, feeder_idx, fpw_idx = span_index_mapping[currentspan]
    # idx 값을 current_structure_list에서 가져오기
    idx_value = current_structure_list[idx]

    return idx_value, comment, feeder_idx, fpw_idx


def get_lateral_offset_and_angle(index, currentspan):
    """ 홀수/짝수 전주에 따른 편위 및 각도 계산 """
    sign = -1 if index % 2 == 1 else 1
    return sign * 0.2, -sign * math.degrees(0.4 / currentspan)


def handle_curve_and_straight_section(pos, next_pos, currentspan, polyline_with_sta, current_airjoint, obj_index,
                                      comment, currnet_type, current_structure, next_structure, param_z, DESIGNSPEED):
    """ 직선, 곡선 구간 wire 처리 """
    lines = []
    sign = -1 if currnet_type == 'I' else 1

    lateral_offset = sign * 0.2
    x, y = get_bracket_coordinates(DESIGNSPEED, 'AJ형_시점')
    x1, y1 = get_bracket_coordinates(DESIGNSPEED, 'F형_시점')
    x2, y2 = get_bracket_coordinates(DESIGNSPEED, 'AJ형_중간1')
    x3, y3 = get_bracket_coordinates(DESIGNSPEED, 'AJ형_중간2')
    x4, y4 = get_bracket_coordinates(DESIGNSPEED, 'AJ형_끝')
    x5, y5 = get_bracket_coordinates(DESIGNSPEED, 'F형_끝')

    # z값 변수 언팩
    current_slope = param_z['current_slope']
    current_pitch = param_z['pitch']
    next_slope = param_z['next_slope']
    next_pitch = param_z['next_pitch']
    current_z = param_z['current_z']
    next_z = param_z['next_z']

    # 구조물 OFFSET 가져오기
    gauge = get_pole_gauge(DESIGNSPEED, current_structure)
    next_gauge = get_pole_gauge(DESIGNSPEED, next_structure)
    # 전차선 정보 가져오기
    contact_object_index, messenger_object_index, system_heigh, contact_height = get_contact_wire_and_massanger_wire_info(
        DESIGNSPEED, current_structure, currentspan)

    # H1 전차선높이
    # H2 조가선 높이

    # 에어조인트 구간 처리
    if current_airjoint == '에어조인트 시작점 (1호주)':

        # 본선
        adjusted_angle = calculate_curve_angle(polyline_with_sta, pos, next_pos, lateral_offset, x)
        lines.append(f'{pos},.freeobj 0;{obj_index};{lateral_offset};0;{adjusted_angle};,;본선\n')

        # 무효선

        slope_degree1, slope_degree2, h1, h2, pererall_d, sta2 = initialrize_tenstion_device(pos, gauge, currentspan,
                                                                                             contact_height,
                                                                                             system_heigh,
                                                                                             adjusted_angle, y1)
        slope_degree2 = calculate_slope(h2, contact_height + system_heigh, currentspan)  # 조가선 상하각도
        slope_degree1 = calculate_slope(h1, contact_height + y1, currentspan)  # 전차선 상하각도
        adjusted_angle = calculate_curve_angle(polyline_with_sta, pos, next_pos, gauge, x1)  # 평면각도
        lines.append(
            f'{sta2},.freeobj 0;{messenger_object_index};{pererall_d};{h2};{adjusted_angle};{slope_degree2},;무효조가선\n')
        lines.append(
            f'{sta2},.freeobj 0;{contact_object_index};{pererall_d};{h1};{adjusted_angle};{slope_degree1},;무효전차선\n')

    elif current_airjoint == '에어조인트 (2호주)':
        # 본선 각도
        adjusted_angle = calculate_curve_angle(polyline_with_sta, pos, next_pos, x, x3)
        lines.append(f"{pos},.freeobj 0;{obj_index};{x};0;{adjusted_angle};,;본선\n")

        # 무효선 하강
        adjusted_angle = calculate_curve_angle(polyline_with_sta, pos, next_pos, x1, x2)  # 평면각도

        adjusted_angle_conatctwire = calculate_slope(contact_height + y1, contact_height, currentspan)  # 전차선상하각도
        adjusted_angle_massangerwire = calculate_slope(contact_height + system_heigh, contact_height + system_heigh,
                                                       currentspan)  # 조가선 상하각도
        '''
        lines.append(f"{pos},.freeobj 0;{contact_object_index};{x1};{contact_height + y1};{adjusted_angle};{adjusted_angle_conatctwire};,;무효전차선\n")
        lines.append(f"{pos},.freeobj 0;{messenger_object_index};{x1};{contact_height + system_heigh};{adjusted_angle};{adjusted_angle_massangerwire};,;무효조가선\n")
        '''
        lines.append(f"{pos},.freeobj 0;{obj_index};{x1};{y1};{adjusted_angle};{adjusted_angle_conatctwire};,;무효선\n")
    elif current_airjoint == '에어조인트 중간주 (3호주)':
        # 본선 >무효선 상승
        adjusted_angle = calculate_curve_angle(polyline_with_sta, pos, next_pos, x3, x5)  # 평면각도
        topdown_angle_conatctwire = calculate_slope(contact_height, contact_height + y1, currentspan)  # 전차선 상하각도
        topdown_angle_massangerwire = calculate_slope(contact_height + system_heigh, contact_height + system_heigh,
                                                      currentspan)  # 조가선 상하각도
        '''
        lines.append(f"{pos},.freeobj 0;{contact_object_index};{x3};0;{adjusted_angle};{topdown_angle_conatctwire};,;본선전차선\n")
        lines.append(f"{pos},.freeobj 0;{messenger_object_index};{x3};0;{adjusted_angle};{topdown_angle_massangerwire};,;본선조가선\n")
        '''
        lines.append(f"{pos},.freeobj 0;{obj_index};{x3};0;{adjusted_angle};{topdown_angle_conatctwire};,;무효선\n")
        # 무효선 >본선
        adjusted_angle = calculate_curve_angle(polyline_with_sta, pos, next_pos, x2, x4)
        lines.append(f"{pos},.freeobj 0;{obj_index};{x2};0;{adjusted_angle};0;,;무효선\n")

    elif current_airjoint == '에어조인트 (4호주)':
        # 본선 각도
        adjusted_angle = calculate_curve_angle(polyline_with_sta, pos, next_pos, x4, -lateral_offset)
        lines.append(f"{pos},.freeobj 0;{obj_index};{x4};0;{adjusted_angle};,;본선\n")

        # H1 전차선높이
        # H2 조가선 높이

        # 무효선

        slope_degree1, slope_degree2, h1, h2, pererall_d, _ = initialrize_tenstion_device(pos, gauge, currentspan,
                                                                                          contact_height, system_heigh,
                                                                                          adjusted_angle, y1)
        topdown_angle_conatctwire = calculate_slope(contact_height + y1, h1, currentspan)  # 전차선 상하각도
        topdown_angle_massangerwire = calculate_slope(contact_height + system_heigh, h2, currentspan)  # 조가선 상하각도
        adjusted_angle = calculate_curve_angle(polyline_with_sta, pos, next_pos, x5, next_gauge)  # 평면각도
        lines.append(
            f'{pos},.freeobj 0;{messenger_object_index};{x5};{contact_height + system_heigh};{adjusted_angle};{topdown_angle_massangerwire};,;무효조가선\n')
        lines.append(
            f'{pos},.freeobj 0;{contact_object_index};{x5};{contact_height + y1};{adjusted_angle};{topdown_angle_conatctwire};,;무효전차선\n')

    # 일반구간
    else:
        adjusted_angle = calculate_curve_angle(polyline_with_sta, pos, next_pos, lateral_offset, -lateral_offset)
        pitch_angle = change_permile_to_degree(current_pitch)
        topdown_angle = calculate_slope(current_z, next_z, currentspan) - pitch_angle  # 전차선 상하각도
        lines.append(f"{pos},.freeobj 0;{obj_index};{lateral_offset};;{adjusted_angle};{topdown_angle};,;{comment}\n")
    return lines


def change_permile_to_degree(permile):
    """퍼밀 값을 도(degree)로 변환"""
    # 정수 또는 문자열이 들어오면 float으로 변환
    if not isinstance(permile, (int, float)):
        permile = float(permile)

    return math.degrees(math.atan(permile / 1000))  # 퍼밀을 비율로 변환 후 계산


def calculate_slope(h1, h2, gauge):
    """주어진 높이 차이와 수평 거리를 바탕으로 기울기(각도) 계산"""
    slope = (h2 - h1) / gauge  # 기울기 값 (비율)
    return math.degrees(math.atan(slope))  # 아크탄젠트 적용 후 degree 변환


def initialrize_tenstion_device(pos, gauge, currentspan, contact_height, system_heigh, adjusted_angle=0, y=0):
    # 장력장치 치수
    tension_device_length = 7.28

    # 전선 각도
    new_length = currentspan - tension_device_length  # 현재 span에서 장력장치까지의 거리
    pererall_d, vertical_offset = return_new_point(gauge, currentspan, tension_device_length)  # 선형 시작점에서 전선까지의 거리

    sta2 = pos + vertical_offset  # 전선 시작 측점
    h1 = 5.563936  # 장력장치 전차선 높이
    h2 = 6.04784  # 장력장치 조가선 높이

    slope_radian1 = math.atan((h1 - (contact_height + y)) / currentspan)  # 전차선 각도(라디안)
    slope_radian2 = math.atan((h2 - (contact_height + system_heigh)) / currentspan)  # 조가선 각도(라디안)

    slope_degree1 = math.degrees(slope_radian1)  # 전차선 각도(도)
    slope_degree2 = math.degrees(slope_radian2)  # 조가선 각도(도)

    return slope_degree1, slope_degree2, h1, h2, pererall_d, sta2


# 새로운 점 계산 함수
def return_new_point(x, y, L):
    A = (x, 0)  # A점 좌표
    B = (0, 0)  # 원점 B
    C = (0, y)  # C점 좌표
    theta = math.degrees(abs(math.atan(y / x)))
    D = calculate_destination_coordinates(A[0], A[1], theta, L)  # 이동한 D점 좌표
    E = B[0], B[1] + D[1]
    d1 = calculate_distance(D[0], D[1], E[0], E[1])
    d2 = calculate_distance(B[0], B[1], E[0], E[1])

    # 외적을 이용해 좌우 판별
    v_x, v_y = C[0] - B[0], C[1] - B[1]  # 선분 벡터
    w_x, w_y = A[0] - B[0], A[1] - B[1]  # 점에서 선분 시작점까지의 벡터
    cross = v_x * w_y - v_y * w_x  # 외적 계산
    sign = -1 if cross > 0 else 1

    return d1 * sign, d2


def calculate_curve_angle(polyline_with_sta, pos, next_pos, stagger1, stagger2):
    point_a, P_A, vector_a = interpolate_coordinates(polyline_with_sta, pos)
    point_b, P_B, vector_b = interpolate_coordinates(polyline_with_sta, next_pos)

    if point_a and point_b:
        offset_point_a = calculate_offset_point(vector_a, point_a, stagger1)
        offset_point_b = calculate_offset_point(vector_b, point_b, stagger2)

        offset_point_a_z = (offset_point_a[0], offset_point_a[1], 0)  # Z값 0추가
        offset_point_b_z = (offset_point_b[0], offset_point_b[1], 0)  # Z값 0추가

        a_b_angle = calculate_bearing(offset_point_a[0], offset_point_a[1], offset_point_b[0], offset_point_b[1])
        finale_anlge = vector_a - a_b_angle
    return finale_anlge


def get_pole_gauge(DESIGNSPEED, current_structure):
    GAUGE_dictionary = {
        150: {'토공': -3, '교량': -3.5, '터널': 2.1},
        250: {'토공': -3, '교량': -3.5, '터널': 2.1},
        350: {'토공': -3.267, '교량': -3.5156, '터널': 2.1}
    }
    gauge = GAUGE_dictionary.get(DESIGNSPEED, {}).get(current_structure, "알 수 없는 구조")
    return gauge


def get_airjoint_angle(gauge, stagger, span):
    S_angle = abs(math.degrees((gauge + stagger) / span)) if span != 0 else 0.0
    E_angle = abs(math.degrees((gauge - stagger) / span)) if span != 0 else 0.0

    return S_angle, E_angle


def get_contact_wire_and_massanger_wire_info(DESIGNSPEED, current_structure, span):
    inactive_contact_wire = {40: 1257, 45: 1258, 50: 1259, 55: 1260, 60: 1261}  # 무효 전차선 인덱스
    inactive_messenger_wire = {40: 1262, 45: 1263, 50: 1264, 55: 1265, 60: 1266}  # 무효 조가선 인덱스

    # 객체 인덱스 가져오기 (기본값 60)
    contact_object_index = inactive_contact_wire.get(span, 1261)
    messenger_object_index = inactive_messenger_wire.get(span, 1266)

    # 가고와 전차선 높이정보
    contact_height_dictionary = {
        150: {'토공': (0.96, 5.2), '교량': (0.96, 5.2), '터널': (0.71, 5)},
        250: {'토공': (1.2, 5.2), '교량': (1.2, 5.2), '터널': (0.85, 5)},
        350: {'토공': (1.4, 5.1), '교량': (1.4, 5.1), '터널': (1.4, 5.1)}
    }

    contact_data = contact_height_dictionary.get(DESIGNSPEED, contact_height_dictionary[250])
    system_heigh, contact_height = contact_data.get(current_structure, (0, 0))  # 기본값 (0, 0) 설정

    return contact_object_index, messenger_object_index, system_heigh, contact_height


def calculate_distance(x1, y1, x2, y2):
    """두 점 (x1, y1)과 (x2, y2) 사이의 유클리드 거리 계산"""
    return math.hypot(x2 - x1, y2 - y1)  # math.sqrt((x2 - x1)**2 + (y2 - y1)**2)와 동일


def interpolate_coordinates(polyline, target_sta):
    """
    주어진 폴리선 데이터에서 특정 sta 값에 대한 좌표를 선형 보간하여 반환.

    :param polyline: [(sta, x, y, z), ...] 형식의 리스트
    :param target_sta: 찾고자 하는 sta 값
    :return: (x, y, z) 좌표 튜플
    """
    # 정렬된 리스트를 가정하고, 적절한 두 점을 찾아 선형 보간 수행
    for i in range(len(polyline) - 1):
        sta1, x1, y1, z1 = polyline[i]
        sta2, x2, y2, z2 = polyline[i + 1]
        v1 = calculate_bearing(x1, y1, x2, y2)
        # target_sta가 두 점 사이에 있는 경우 보간 수행
        if sta1 <= target_sta < sta2:
            t = abs(target_sta - sta1)
            x, y = calculate_destination_coordinates(x1, y1, v1, t)
            z = z1 + t * (z2 - z1)
            return (x, y, z), (x1, y1, z1), v1

    return None  # 범위를 벗어난 sta 값에 대한 처리


# 폴리선 좌표 읽기
def read_polyline(file_path):
    points = []
    with open(file_path, 'r') as file:
        for line in file:
            # 쉼표로 구분된 값을 읽어서 float로 변환
            x, y, z = map(float, line.strip().split(','))
            points.append((x, y, z))
    return points


def find_last_block(data):
    last_block = None  # None으로 초기화하여 값이 없을 때 오류 방지

    for line in data:
        if isinstance(line, str):  # 문자열인지 확인
            match = re.search(r'(\d+),', line)
            if match:
                last_block = int(match.group(1))  # 정수 변환하여 저장

    return last_block  # 마지막 블록 값 반환


def read_file():
    root = tk.Tk()
    root.withdraw()  # Tkinter 창을 숨김
    file_path = filedialog.askopenfilename(defaultextension=".txt",
                                           filetypes=[("txt files", "curve_info.txt"), ("All files", "*.*")])

    if not file_path:
        print("파일을 선택하지 않았습니다.")
        return []

    print('현재 파일:', file_path)

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.read().splitlines()  # 줄바꿈 기준으로 리스트 생성
    except UnicodeDecodeError:
        print('현재 파일은 UTF-8 인코딩이 아닙니다. EUC-KR로 시도합니다.')
        try:
            with open(file_path, 'r', encoding='euc-kr') as file:
                lines = file.read().splitlines()
        except UnicodeDecodeError:
            print('현재 파일은 EUC-KR 인코딩이 아닙니다. 파일을 읽을 수 없습니다.')
            return []

    return lines


# 추가
# 방위각 거리로 점 좌표반환
def calculate_destination_coordinates(x1, y1, bearing, distance):
    # Calculate the destination coordinates given a starting point, bearing, and distance in Cartesian coordinates
    angle = math.radians(bearing)
    x2 = x1 + distance * math.cos(angle)
    y2 = y1 + distance * math.sin(angle)
    return x2, y2


# offset 좌표 반환
def calculate_offset_point(vector, point_a, offset_distance):
    if offset_distance > 0:  # 우측 오프셋
        vector -= 90
    else:
        vector += 90  # 좌측 오프셋
    offset_a_xy = calculate_destination_coordinates(point_a[0], point_a[1], vector, abs(offset_distance))
    return offset_a_xy


def calculate_bearing(x1, y1, x2, y2):
    # Calculate the bearing (direction) between two points in Cartesian coordinates
    dx = x2 - x1
    dy = y2 - y1
    bearing = math.degrees(math.atan2(dy, dx))
    return bearing


# 실행
def load_structure_data():
    """구조물 데이터를 엑셀 파일에서 불러오는 함수"""
    openexcelfile = open_excel_file()
    if openexcelfile:
        return find_structure_section(openexcelfile)
    else:
        print("엑셀 파일을 선택하지 않았습니다.")
        return None


def load_curve_data():
    """곡선 데이터를 텍스트 파일에서 불러오는 함수"""
    txt_filepath = 'c:/temp/curve_info.txt'
    if txt_filepath:
        return find_curve_section(txt_filepath)
    else:
        print("지정한 파일을 찾을 수 없습니다.")
        return None


def load_pitch_data():
    """곡선 데이터를 텍스트 파일에서 불러오는 함수"""
    txt_filepath = 'c:/temp/pitch_info.txt'
    if txt_filepath:
        return find_pitch_section(txt_filepath)
    else:
        print("지정한 파일을 찾을 수 없습니다.")
        return None


def load_coordinates():
    """BVE 좌표 데이터를 텍스트 파일에서 불러오는 함수"""
    coord_filepath = 'c:/temp/bve_coordinates.txt'
    return read_polyline(coord_filepath)


def save_pole_data(pole_positions, structure_list, curve_list, pitchlist, DESIGNSPEED, airjoint_list, polyline, filename="c:/temp/전주.txt"):
    """전주 데이터를 텍스트 파일로 저장하는 함수"""
    save_to_txt(pole_positions, structure_list, curve_list, pitchlist, DESIGNSPEED, airjoint_list, polyline,
                filename)
    print(f"✅ 전주 데이터가 {filename} 파일로 저장되었습니다!")


def save_wire_data(DESIGNSPEED, pole_positions, spans, structure_list, curvelist, pitchlist, polyline, airjoint_list, filename="c:/temp/전차선.txt"):
    """전차선 데이터를 텍스트 파일로 저장하는 함수"""
    process_to_WIRE(DESIGNSPEED, pole_positions, spans, structure_list, curvelist, pitchlist, polyline, airjoint_list,filename)
    print(f"✅ 전차선 데이터가 {filename} 파일로 저장되었습니다!")


def createtxt(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        for line in data:
            f.write(f'{line}\n')


def get_designspeed():
    """사용자로부터 설계 속도를 입력받아 반환"""
    while True:
        try:
            DESIGNSPEED = int(input('프로젝트의 설계속도 입력 (150, 250, 350): '))
            if DESIGNSPEED not in (150, 250, 350):
                print('올바른 DESIGNSPEED 값을 입력하세요 (150, 250, 350)')
            else:
                return DESIGNSPEED
        except ValueError:
            print("숫자를 입력하세요.")


def get_dxf_scale(scale=None):
    """
    도면 축척을 반환하는 함수
    :param scale: 도면 축척 값 (예: 1000 -> 1, 500 -> 0.5)
    :return: 변환된 축척 값 (1:1000 -> 1, 1:500 -> 0.5)
    """
    if scale is None:
        try:
            H_scale = int(input('프로젝트의 평면축척 입력 (예: 1000 -> 1, 500 -> 0.5): '))
            V_scale = int(input('프로젝트의 종단축척 입력 (예: 1000 -> 1, 500 -> 0.5): '))
        except ValueError:
            print("❌ 잘못된 입력! 숫자를 입력하세요.")
            return None

    if H_scale <= 0 or V_scale <= 0:
        print("❌ 축척 값은 양수여야 합니다!")
        return None
    H_scale = H_scale / 1000
    V_scale = 1000 / V_scale

    return H_scale, V_scale


def main():
    """전체 작업을 관리하는 메인 함수"""
    # 고속철도인지 확인

    DESIGNSPEED = get_designspeed()

    # 파일 읽기 및 데이터 처리
    data = read_file()
    last_block = find_last_block(data)
    start_km = 0
    end_km = last_block // 1000
    spans, pole_positions = distribute_pole_spacing_flexible(start_km, end_km)

    # 구조물 정보 로드
    structure_list = load_structure_data()
    if structure_list:
        print("구조물 정보가 성공적으로 로드되었습니다.")

    # 곡선 정보 로드
    curvelist = load_curve_data()
    if curvelist:
        print("곡선 정보가 성공적으로 로드되었습니다.")
    # 기울기 정보 로드
    pitchlist = load_pitch_data()
    if pitchlist:
        print("기울기선 정보가 성공적으로 로드되었습니다.")
    # BVE 좌표 로드
    polyline = load_coordinates()

    airjoint_list = define_airjoint_section(pole_positions)

    # 전주번호 추가
    post_number_lst = generate_postnumbers(pole_positions)

    # 데이터 저장
    save_pole_data(pole_positions, structure_list, curvelist, pitchlist, DESIGNSPEED, airjoint_list, polyline)
    save_wire_data(DESIGNSPEED, pole_positions, spans, structure_list, curvelist, pitchlist, polyline, airjoint_list)
    # createtxt('c:/temp/airjoint_list.txt', airjoint_list)
    print("전주와 전차선 txt가 성공적으로 저장되었습니다.")
    print("도면 작성중.")
    # 도면 스케일
    global scale, H_scale, V_scale
    H_scale, V_scale = get_dxf_scale()
    # 도면 작성
    while True:
        try:
            # 전차선로평면도
            doc, msp = create_new_dxf()
            doc, msp = crate_pegging_plan_mast_and_bracket(doc, msp, polyline, pole_positions, structure_list,
                                                           curvelist, pitchlist, airjoint_list)
            doc, msp = crate_pegging_plan_wire(doc, msp, polyline, pole_positions, structure_list, curvelist, pitchlist,
                                               airjoint_list)
            # 전차선로종단면도
            doc1, msp1 = create_new_dxf()
            doc1, msp1 = create_pegging_profile_mast_and_bracket(doc1, msp1, polyline, pole_positions, structure_list,
                                                                 curvelist, pitchlist, airjoint_list)
            doc1, msp1 = create_pegging_profile_wire(doc1, msp1, polyline, pole_positions, structure_list,
                                                     curvelist, pitchlist, airjoint_list)
            break
        except Exception as e:
            print(f'도면 생성중 에러 발생: {e}')

    # 도면 저장
    while True:
        try:
            save_to_dxf(doc, file_name='c:/temp/pegging_plan.dxf')
            save_to_dxf(doc1, file_name='c:/temp/pegging_profile.dxf')
            print("도면이 성공적으로 저장되었습니다.")
            break
        except Exception as e:
            print(f'도면 저장중 에러가 발생하였습니다. : {e}')

    # 최종 출력
    print(f"전주 개수: {len(pole_positions)}")
    print(f"마지막 전주 위치: {pole_positions[-1]}m (종점: {int(end_km * 1000)}m)")
    print('모든 작업 완료')


# 실행
if __name__ == "__main__":
    main()