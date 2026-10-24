# main_local.py
import logging
import sys

from visual.mappapp import MapVisualizer

logger = logging.getLogger(__name__)


def main() -> int:
    try:
        visualizer = MapVisualizer()
    except Exception:
        logger.exception("MapVisualizer 초기화 실패")
        return 1

    try:
        visualizer.mainloop()
    except KeyboardInterrupt:
        logger.info("사용자 중단")
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sys.exit(main())