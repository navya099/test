"""DXF 캐시 + 쓰기 (HATCH 포함)."""
from __future__ import annotations
from typing import Optional

from tkinter import messagebox
import ezdxf

from core.models import TunnelParams
from services.dxf2.document import DocumentParams


class DxfCache:
    def __init__(self):
        self.path: Optional[str] = None
        self.entities: Optional[list] = None

    def load(self, path: str, force: bool = False):
        if not force and path == self.path and self.entities is not None:
            return self.entities
        try:
            doc = ezdxf.readfile(path)
        except (FileNotFoundError, IOError) as e:
            messagebox.showwarning("DXF 로드 실패", f"{path}\n{e}")
            self.path, self.entities = None, None
            return None
        self.path = path
        self.entities = list(doc.modelspace())
        return self.entities


def write_dxf(path: str, ax, params: TunnelParams, hatch_style: str, doc_params=None):
    """
        표준 DXF 기반 저장 (v2).
        - 표준 템플릿(도곽/표제란/스타일/블록) 자동 로드
        - 타입별 빌더가 형상/치수 담당
        """
    from services.dxf2 import (
        is_standard_available, write_document, get_builder,
    )
    if doc_params is None:
        doc_params = DocumentParams()

    if is_standard_available():
        # ★ 표준 DXF 로드 방식 (v2)
        try:
            builder = get_builder(params.kind)  # 미등록이면 NotImplementedError
        except NotImplementedError as e:
            raise NotImplementedError(f"{e}")
        write_document(path, params, doc_params, builder)
    else:
        # 폴백: 기존 방식
        from services.dxf.wirte import write_document as _old_write
        _old_write(path, ax, params, hatch_style=hatch_style)

