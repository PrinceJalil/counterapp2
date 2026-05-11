from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel


class LogItem(QWidget):
    def __init__(self, icon: str, title: str, status: str, time_str: str, parent=None):
        super().__init__(parent)
        self.setProperty("class", "log-item")
        self._build_ui(icon, title, status, time_str)

    def _build_ui(self, icon: str, title: str, status: str, time_str: str):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 16px; color: #35e192;")

        text_col = QVBoxLayout()
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size: 12px; font-weight: bold; color: #e2e2e9;")
        status_lbl = QLabel(status)
        status_lbl.setStyleSheet("font-size: 10px; color: #8b919e;")
        text_col.addWidget(title_lbl)
        text_col.addWidget(status_lbl)

        time_lbl = QLabel(time_str)
        time_lbl.setStyleSheet("font-size: 11px; color: #8b919e; font-family: monospace;")

        layout.addWidget(icon_lbl)
        layout.addLayout(text_col)
        layout.addStretch()
        layout.addWidget(time_lbl)
