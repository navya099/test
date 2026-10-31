"""python -m railway_alignment 진입점"""
import logging

from src.railway_alignment.cli import main_gui

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)

if __name__ == "__main__":
    main_gui()