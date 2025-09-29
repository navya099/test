class BlockManager:
    def __init__(self, doc):
        self.doc = doc

    def define_iptable_blocks(self):
        blk = self.doc.blocks.new(name="IPTABLE")
        layer = 'IPTABLE'
        color = 1
        height = 3
        style = "Gulim"
        #테두리
        blk.add_line((0, 0), (51, 0), dxfattribs={'color': color, 'layer': layer}) #하단 테두리
        blk.add_line((51, 0), (51, 51), dxfattribs={'color': color, 'layer': layer})#우측 테두리
        blk.add_line((51, 51), (0, 51), dxfattribs={'color': color, 'layer': layer})#상단 테두리
        blk.add_line((0, 51), (0, 0), dxfattribs={'color': color, 'layer': layer})#좌측테두리
        #태이블 내부 가로선
        blk.add_line((0, 7), (51, 7), dxfattribs={'color': color, 'layer': layer})
        blk.add_line((0, 14), (51, 14), dxfattribs={'color': color, 'layer': layer})
        blk.add_line((0, 21), (51, 21), dxfattribs={'color': color, 'layer': layer})
        blk.add_line((0, 28), (51, 28), dxfattribs={'color': color, 'layer': layer})
        blk.add_line((0, 35), (51, 35), dxfattribs={'color': color, 'layer': layer})
        blk.add_line((0, 42), (51, 42), dxfattribs={'color': color, 'layer': layer})
        #테이블 내부 세로선
        blk.add_line((12, 42), (12, 0), dxfattribs={'color': color, 'layer': layer})
        #테이블 내부 문자
        blk.add_text('IA',
                          dxfattribs={
                              'insert': (3, 37),
                              'height': height,
                              'color': color,
                              'layer': layer,
                              'style': style,
                          })
        blk.add_text('R',
                     dxfattribs={
                         'insert': (4.5, 30),
                         'height': height,
                         'color': color,
                         'layer': layer,
                         'style': style
                     })
        blk.add_text('TL',
                     dxfattribs={
                         'insert': (3, 23),
                         'height': height,
                         'color': color,
                         'layer': layer,
                         'style': style
                     })
        blk.add_text('CL',
                     dxfattribs={
                         'insert': (3, 16),
                         'height': height,
                         'color': color,
                         'layer': layer,
                         'style': style
                     })
        blk.add_text('X',
                     dxfattribs={
                         'insert': (4.5, 9),
                         'height': height,
                         'color': color,
                         'layer': layer,
                         'style': style
                     })
        blk.add_text('Y',
                     dxfattribs={
                         'insert': (4.5, 2),
                         'height': height,
                         'color': color,
                         'layer': layer,
                         'style': style
                     })
        # IPNO 속성
        blk.add_attdef(tag="IPNO", insert=(18, 44), height=3, text="0", dxfattribs={'layer': 'attr', 'color': color, 'style': style})
        # IA 속성
        blk.add_attdef(tag="IA", insert=(14.25, 38.5), height=3, text="0", dxfattribs={'layer': 'attr', 'color': color, 'style': style})
        # R 속성
        blk.add_attdef(tag="R", insert=(14.25, 31.5), height=3, text="0", dxfattribs={'layer': 'attr', 'color': color, 'style': style})
        # TL 속성
        blk.add_attdef(tag="TL", insert=(14.25, 24.5), height=3, text="0", dxfattribs={'layer': 'attr', 'color': color, 'style': style})
        # CL 속성
        blk.add_attdef(tag="CL", insert=(14.25, 17.5), height=3, text="0", dxfattribs={'layer': 'attr', 'color': color, 'style': style})
        # X 속성
        blk.add_attdef(tag="X", insert=(14.25, 10.55), height=3, text="0", dxfattribs={'layer': 'attr', 'color': color, 'style': style})
        # Y 속성
        blk.add_attdef(tag="Y", insert=(14.25, 3.5), height=3, text="0", dxfattribs={'layer': 'attr', 'color': color, 'style': style})

    def define_curvespec_blocks(self):
        blk = self.doc.blocks.new(name="곡선인출블럭")
        layer = '곡선제원'
        color = 1
        height = 3
        style = "Gulim"
        #인출선
        blk.add_line((0, 0), (70, 0), dxfattribs={'color': color, 'layer': layer})
        #인출텍스트
        #곡선제원문자속성
        blk.add_attdef(tag="type", insert=(30, 0.5), height=height, text="0", dxfattribs={'layer': 'attr', 'color':color, 'style': style})
        # 곡선위치속성
        blk.add_attdef(tag="sta", insert=(40, 0.5), height=height, text="0", dxfattribs={'layer': 'attr', 'color': color, 'style': style})

    def define_station_marker(self):
        blk = self.doc.blocks.new(name="정거장중심표")
        layer = '정거장중심표'
        color = 1
        height = 3


        # 인출선
        blk.add_line((0, 0), (70, 0), dxfattribs={'color': color, 'layer': layer})
        #정거장원
        # 아래반원 HATCH
        hatch = blk.add_hatch(color=1)  # 빨강
        path = hatch.paths.add_edge_path()
        center = (15, 0)
        radius = 2
        # ARC: -90° ~ 90° (시계 반대 방향으로)
        blk.add_arc(center=center, radius=radius, start_angle=0, end_angle=180, dxfattribs={'color': color})
        # ARC: -90° ~ 90° (시계 반대 방향으로)
        path.add_arc(center=center, radius=radius, start_angle=180, end_angle=360, ccw=True)

        # 2️⃣ 직선: 오른쪽 끝점 → 왼쪽 끝점 (반원 닫기)
        start_pt = (center[0] + radius, center[1])  # (17, 0)
        end_pt = (center[0] - radius, center[1])  # (13, 0)
        path.add_line(start_pt, end_pt)

        #정거장명 속성
        blk.add_attdef(tag="name", insert=(30, 0.5), height=height, text="0", dxfattribs={'layer': 'attr', 'style': 'Gulim', 'color' : color})
        #km 속성
        blk.add_attdef(tag="sta", insert=(30, -3.5), height=height, text="0", dxfattribs={'layer': 'attr', 'style': 'Gulim', 'color': color})
