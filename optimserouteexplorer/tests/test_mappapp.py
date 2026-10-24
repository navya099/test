# tests/test_mappapp.py
import unittest


class TestMappappImports(unittest.TestCase):
    def test_import(self):
        """모듈 import 가능 (tkinter 없이 import 시 위험)."""
        try:
            from visual import mappapp
            self.assertTrue(hasattr(mappapp, "MapVisualizer"))
        except ImportError as e:
            self.skipTest(f"GUI 의존성 없음: {e}")


if __name__ == "__main__":
    unittest.main()