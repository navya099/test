from dataclasses import dataclass

@dataclass
class BVEImageData:
    """csv용 이미지 데이터 컨테이너"""
    km_string: str = ''
    m_string: str = ''
    imgname: str = ''
    img_bg_color: tuple[int,int,int] = ()
    txt_color: tuple[int,int,int] = ()
    openfile_name: str = ''