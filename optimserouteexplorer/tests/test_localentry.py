# tests/test_localentry.py
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from local.localentry import compute, ProcessResult


class TestCompute(unittest.TestCase):
    @patch("local.localentry.run_process")
    @patch("local.localentry.format_top10")
    def test_compute_returns_process_result(self, mock_format, mock_run):
        """compute 가 ProcessResult 반환, 파일 I/O 없음."""
        mock_run.return_value = [{"fake": "candidate"}]
        mock_format.return_value = [{"ID": 0, "fitness": 75.0}]

        result = compute(
            start=(37.5, 127.0), end=(37.6, 127.1),
            n_candidates=3, n_generations=1, top_n=10, chain=40,
        )

        self.assertIsInstance(result, ProcessResult)
        self.assertEqual(result.top, [{"ID": 0, "fitness": 75.0}])
        self.assertEqual(result.raw, [{"fake": "candidate"}])
        mock_run.assert_called_once()
        mock_format.assert_called_once()


class TestOutputs(unittest.TestCase):
    @patch("local.localentry.export_excel_report")
    def test_export_excel_creates_dir(self, mock_export):
        """export_excel 이 디렉토리 생성 후 호출."""
        from local.localentry import export_excel

        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "sub" / "report.xlsx"
            export_excel([{"ID": 0}], path)
            self.assertTrue(path.parent.exists())
            mock_export.assert_called_once()

    @patch("local.localentry.visualize_routes_with_button")
    def test_export_visualization(self, mock_vis):
        """export_visualization 호출 검증."""
        from local.localentry import export_visualization

        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "map.html"
            export_visualization(
                [{"ID": 0}], start=(37.5, 127.0), end=(37.6, 127.1),
                top_n=1, path=path,
            )
            mock_vis.assert_called_once()

    @patch("local.localentry.BVEProcess")
    def test_run_bve_empty(self, mock_bve):
        """빈 결과 → BVE 생략."""
        from local.localentry import run_bve

        run_bve([])
        mock_bve.assert_not_called()

    @patch("local.localentry.BVEProcess")
    def test_run_bve_with_results(self, mock_bve):
        """결과 있으면 BVE 호출."""
        from local.localentry import run_bve

        run_bve([{"plan": "x"}])
        mock_bve.assert_called_once()


if __name__ == "__main__":
    unittest.main()