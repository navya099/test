# main_web.py
import logging
import os
import sys

from web.app import create_app

logger = logging.getLogger(__name__)


def main() -> int:
    debug = os.environ.get("WEB_DEBUG", "0") == "1"
    app = create_app({"DEBUG": debug})

    host = os.environ.get("WEB_HOST", "127.0.0.1")
    port = int(os.environ.get("WEB_PORT", "5000"))

    if debug:
        logger.warning("개발 모드(debug=True) — 배포 시 사용 금지")

    app.run(host=host, port=port, debug=debug, use_reloader=False)
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sys.exit(main())