import os

from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QFileDialog, QLineEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor, QPixmap

from utils.helpers import get_asset_path


class SourceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Source")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(460, 394)

        self.chosen_source = None
        self._init_ui()

    def _init_ui(self):
        outer = QWidget(self)
        outer.setObjectName("dialog-card")
        outer.setGeometry(0, 0, 460, 394)
        outer.setStyleSheet("""
            #dialog-card {
                background-color: #1a1b21;
                border: 1px solid #33353a;
                border-radius: 16px;
            }
        """)

        root = QVBoxLayout(outer)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(0)

        # Header
        hdr = QHBoxLayout()
        title = QLabel("Select Source")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #e2e2e9;")
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet("""
            QPushButton { background: #282a2f; color: #8b919e; border: none;
                          border-radius: 14px; font-size: 13px; }
            QPushButton:hover { background: #93000a; color: #fff; }
        """)
        close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        close_btn.clicked.connect(self.reject)
        hdr.addWidget(title)
        hdr.addStretch()
        hdr.addWidget(close_btn)
        root.addLayout(hdr)
        root.addSpacing(8)

        sub = QLabel("Pilih sumber video untuk memulai counting.")
        sub.setStyleSheet("font-size: 12px; color: #8b919e;")
        root.addWidget(sub)
        root.addSpacing(28)

        # Option cards
        self._btn_video = self._make_option_btn(
            "Video File", "Unggah file video (mp4/avi)", get_asset_path("file.png")
        )
        self._btn_webcam = self._make_option_btn(
            "Webcam", "Gunakan kamera bawaan / eksternal", get_asset_path("webcam.png")
        )


        root.addWidget(self._btn_video)
        root.addSpacing(10)
        root.addWidget(self._btn_webcam)

        root.addStretch()

    def _make_option_btn(self, label: str, desc: str, icon_path: str) -> QFrame:
        card = QFrame()
        card.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        card.setObjectName("opt-card")
        card.setStyleSheet("""
            #opt-card {
                background-color: #282a2f;
                border: 1px solid #33353a;
                border-radius: 10px;
            }
            #opt-card:hover {
                background-color: #2e3039;
                border: 1px solid #3D8EF0;
            }
        """)
        card.setFixedHeight(64)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(18, 0, 18, 0)
        layout.setSpacing(14)

        icon_lbl = QLabel()
        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            icon_lbl.setPixmap(pixmap.scaled(
                24, 24,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
        else:
            icon_lbl.setText("📁")
            icon_lbl.setStyleSheet("font-size: 22px; color: #3D8EF0;")
        icon_lbl.setFixedWidth(30)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        text_col.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        name_lbl = QLabel(label)
        name_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #e2e2e9;")
        desc_lbl = QLabel(desc)
        desc_lbl.setStyleSheet("font-size: 11px; color: #8b919e;")
        text_col.addWidget(name_lbl)
        text_col.addWidget(desc_lbl)

        arrow = QLabel("›")
        arrow.setStyleSheet("font-size: 20px; color: #414752;")

        layout.addWidget(icon_lbl)
        layout.addLayout(text_col)
        layout.addStretch()
        layout.addWidget(arrow)

        card.mousePressEvent = lambda e, b=label: self._card_clicked(b)
        return card

    def _card_clicked(self, label: str):
        if label == "Video File":
            self._pick_video()
        elif label == "Webcam":
            self._pick_webcam()


    def _pick_video(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Video File", "",
            "Video Files (*.mp4 *.avi *.mkv *.mov *.wmv)"
        )
        if file_path:
            self.chosen_source = file_path
            self.accept()

    def _pick_webcam(self):
        self.chosen_source = 0
        self.accept()

