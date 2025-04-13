from dataclasses import dataclass, field
from typing import List, Optional
from tkinter import filedialog, ttk
import xml.etree.ElementTree as ET

@dataclass
class Line:
    start: str
    end: str
    direction: Optional[float] = None
    length: Optional[float] = None

@dataclass
class Spiral:
    start: str
    end: str
    spi_type: Optional[str]
    length: Optional[float]
    radius_start: Optional[float]
    radius_end: Optional[float]
    rot: Optional[str]

@dataclass
class Curve:
    start: str
    end: str
    radius: Optional[float]
    length: Optional[float]
    rot: Optional[str]

@dataclass
class CoordGeom:
    lines: List[Line] = field(default_factory=list)
    spirals: List[Spiral] = field(default_factory=list)
    curves: List[Curve] = field(default_factory=list)

@dataclass
class PVI:
    station: float
    elevation: float

@dataclass
class ParaCurve:
    length: float
    station: float
    elevation: float

@dataclass 
class ProfAlign:
    name: str
    pvis: List[PVI] = field(default_factory=list)
    paracurves: List[ParaCurve] = field(default_factory=list)
    
@dataclass
class Profile:
    name: str
    profalign: ProfAlign


    

    
@dataclass
class Alignment:
    name: str
    length: Optional[float]
    coord_geom: CoordGeom
    profile: Profile
    

    
def parse_alignment(alignment_elem, ns) -> Alignment:
    name = alignment_elem.attrib.get('name', '')
    length = float(alignment_elem.attrib.get('length', '0'))

    coord_geom = parse_code_geom(alignment_elem, ns)
    profile = parse_profile(alignment_elem, ns)
    
    return Alignment(name=name, length=length,
                     profile=profile, coord_geom=coord_geom)

def parse_code_geom(alignment_elem, ns) -> CoordGeom:
    #coord_geom 파싱
    coord_geom = CoordGeom()
    coord_geom_elem = alignment_elem.find('lx:CoordGeom', ns)
    if coord_geom_elem is not None:
        for geom in coord_geom_elem:
            tag = geom.tag.split('}')[1]
            if tag == 'Line':
                line = Line(
                    start=geom.find('lx:Start', ns).text,
                    end=geom.find('lx:End', ns).text,
                    direction=float(geom.attrib.get('dir', '0')),
                    length=float(geom.attrib.get('length', '0')),
                )
                coord_geom.lines.append(line)
            elif tag == 'Spiral':
                spiral = Spiral(
                    start=geom.find('lx:Start', ns).text,
                    end=geom.find('lx:End', ns).text,
                    spi_type=geom.attrib.get('spiType'),
                    length=float(geom.attrib.get('length', '0')),
                    radius_start=float(geom.attrib.get('radiusStart', 'inf')),
                    radius_end=float(geom.attrib.get('radiusEnd', 'inf')),
                    rot=geom.attrib.get('rot'),
                )
                coord_geom.spirals.append(spiral)
            elif tag == 'Curve':
                curve = Curve(
                    start=geom.find('lx:Start', ns).text,
                    end=geom.find('lx:End', ns).text,
                    radius=float(geom.attrib.get('radius', '0')),
                    length=float(geom.attrib.get('length', '0')),
                    rot=geom.attrib.get('rot'),
                )
                coord_geom.curves.append(curve)
    return coord_geom

def parse_profile(alignment_elem, ns) -> Profile:
    
    profile_elem = alignment_elem.find('lx:Profile', ns)
    profile_name = profile_elem.attrib.get('name', '')
    
    profalign_elem = profile_elem.find('lx:ProfAlign', ns)
    profalign_name = profalign_elem.attrib.get('name', '')
    print(profalign_name)
    profalign = ProfAlign(name=profalign_name)
    for pvi_elem in profalign_elem.findall('lx:PVI', ns):
        text = pvi_elem.text.strip() if pvi_elem.text else ''
        print(text)
        parts = text.split()
        if len(parts) >= 2:
            station = float(parts[0])
            print(station)
            elevation = float(parts[1])
            print(elevation)
            pvi = PVI(station=station, elevation=elevation)
            profalign.pvis.append(pvi)
            
    for paracurve_elem in profalign_elem.findall('lx:ParaCurve', ns):
        text = paracurve_elem.text.strip() if pvi_elem.text else ''
        length = paracurve_elem.attrib.get('length', '0')
        print(text)
        print(length)
        parts = text.split()
        if len(parts) >= 2:
            station = float(parts[0])
            print(station)
            elevation = float(parts[1])
            print(elevation)
            paracurve = ParaCurve(length=length, station=station, elevation=elevation)
            profalign.paracurves.append(paracurve)
    
    return Profile(name=profile_name,profalign=profalign)

def parse_landxml(filepath: str) -> List[Alignment]:
    tree = ET.parse(filepath)
    root = tree.getroot()
    ns = {'lx': 'http://www.landxml.org/schema/LandXML-1.2'}

    alignments = []
    for alignment_elem in root.findall('.//lx:Alignment', ns):
        alignment = parse_alignment(alignment_elem, ns)
        alignments.append(alignment)

    return alignments

#파일 읽기 함수
def read_file():
    global lines
     # Hide the main window
    file_path = filedialog.askopenfilename()  # Open file dialog
    return file_path

file_path = read_file()
alignments = parse_landxml(file_path)
for al in alignments:
    print(f"{al.name} - {al.length}m")
    for line in al.coord_geom.lines:
        print(f"  Line: {line.start} → {line.end}, Length: {line.length}")
    for spiral in al.coord_geom.spirals:
        print(f"  Spiral: {spiral.spi_type}, R: {spiral.radius_start} → {spiral.radius_end}")
    for curve in al.coord_geom.curves:
        print(f"  Curve: Radius {curve.radius}, Rot: {curve.rot}")
        
    print(f"상위선형 이름: {al.profile.name}")
    print(f"종단선형 이름: {al.profile.profalign.name}")
    print(f"종곡선")
    for paracurve in al.profile.profalign.paracurves:
        print(f"  ParaCurve: length {paracurve.length}, sta {paracurve.station}, elevation: {paracurve.elevation}")
    print(f"PVI")
    for pvi in al.profile.profalign.pvis:
        print(f"  PVI: sta {pvi.station}, elevation: {pvi.elevation}")
