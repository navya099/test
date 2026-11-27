"""Run with python -m railspan and open the printed loopback URL."""
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .engine import EXAMPLE, generate
from .ifc_export import export_ifc
from .obstacle_csv import example_csv, read_obstacles
from .profile_csv import EXAMPLES as ALIGNMENT_EXAMPLES, alignment_example, read_cant, read_plan, read_profile

CSV_IMPORTS = {
    "/obstacles/import": read_obstacles, "/profiles/import": read_profile,
    "/plan/import": read_plan, "/cant/import": read_cant,
}


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, content, mime):
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(content)

    def json_reply(self, status, value):
        self.reply(status, json.dumps(value, ensure_ascii=False).encode(), "application/json; charset=utf-8")

    def do_GET(self):
        if self.path == "/":
            self.reply(200, Path(__file__).with_name("index.html").read_bytes(), "text/html; charset=utf-8")
        elif self.path == "/example":
            self.json_reply(200, EXAMPLE)
        elif self.path == "/obstacles-example.csv":
            self.reply(200, example_csv(), "text/csv; charset=utf-8")
        elif self.path in ALIGNMENT_EXAMPLES:
            self.reply(200, alignment_example(*ALIGNMENT_EXAMPLES[self.path]), "text/csv; charset=utf-8")
        else:
            self.send_error(404)

    def do_POST(self):
        importer = CSV_IMPORTS.get(self.path)
        if importer is None and self.path not in ("/generate", "/export/ifc"):
            self.send_error(404)
            return
        expected = "text/csv" if importer else "application/json"
        if self.headers.get_content_type() != expected:
            self.send_error(415)
            return
        exporting = self.path == "/export/ifc"
        if exporting:
            try:
                import ifcopenshell
            except ModuleNotFoundError:
                self.json_reply(503, {"error": "IFC 내보내기 전에 python -m pip install -r railspan/requirements-ifc.txt 를 실행하세요."})
                return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 200_000:
                raise ValueError("프로젝트 데이터 크기를 확인하세요.")
            payload = self.rfile.read(size)
            result = importer(payload) if importer else generate(json.loads(payload))
        except (TypeError, ValueError) as error:
            self.json_reply(400, {"error": str(error)})
            return
        if exporting:
            try:
                content = export_ifc(result, ifcopenshell)
            except ImportError:
                self.json_reply(503, {"error": "EPSG를 포함해 내보내려면 python -m pip install -r railspan/requirements-ifc.txt 를 실행하세요."})
                return
            except ValueError as error:
                self.json_reply(400, {"error": str(error)})
                return
            self.reply(200, content, "application/x-step")
        else:
            self.json_reply(200, result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    with ThreadingHTTPServer(("127.0.0.1", args.port), Handler) as server:
        print(f"http://127.0.0.1:{server.server_port}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
