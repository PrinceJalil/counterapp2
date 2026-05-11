import sys
import os

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QIcon

from ui.main_window import MainWindow


def load_stylesheet(app: QApplication) -> None:
    qss_path = os.path.join(os.path.dirname(__file__), "styles", "main_style.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())


def main() -> None:
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), "assets", "iconapp.ico")))
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    load_stylesheet(app)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
