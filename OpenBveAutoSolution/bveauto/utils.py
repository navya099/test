# bveauto/utils.py
from pathlib import Path

from file_io_utils import copy_files, copy_all_files


def copy_post_assets(ctx, work: Path, source: Path, target: Path,
                     index_names: list[str]):
    """route에 index/post 복사 + target에 이미지/결과물 복사."""
    files = [work / n for n in index_names]
    copy_files(files, ctx.paths.route)

    copy_all_files(
        source, target,
        ['.jpg', '.jpeg'],
        ['.csv', '.png', '.txt'],
        delete_source=False, delete_target=False,
    )
    copy_all_files(
        work, target,
        ['.csv', '.png', '.txt', '.jpg', '.jpeg'],
        ['.dxf', '.ai'],
    )