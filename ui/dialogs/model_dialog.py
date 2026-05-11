import os

from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor


class ModelUploadDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.model_path = ""
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(400, 200)

        outer = QWidget(self)
        outer.setObjectName("dlg-card")
        outer.setGeometry(0, 0, 400, 200)
        outer.setStyleSheet(
            "#dlg-card { background-color: #1a1b21; border: 1px solid #33353a; border-radius: 16px; }"
        )

        root = QVBoxLayout(outer)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(12)

        title = QLabel("Upload YOLO Model")
        title.setStyleSheet("font-size: 15px; font-weight: 700; color: #e2e2e9;")
        root.addWidget(title)

        sub = QLabel("Versi model min yolov8n dengan format .pt/.onnx")
        sub.setStyleSheet("font-size: 11px; color: #8b919e;")
        root.addWidget(sub)

        self.lbl_path = QLabel("Belum ada model dipilih")
        self.lbl_path.setStyleSheet("color:#8b919e; font-size:12px; font-style:italic;")

        btn_pick = QPushButton("Browse File...")
        btn_pick.setStyleSheet("background:#282a2f; color:#e2e2e9; padding:6px 12px; border-radius:4px;")
        btn_pick.clicked.connect(self._browse)

        row = QHBoxLayout()
        row.addWidget(btn_pick)
        row.addWidget(self.lbl_path, stretch=1)
        root.addLayout(row)
        root.addStretch()

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Batal")
        btn_cancel.setStyleSheet("background:transparent; color:#8b919e; padding:8px 16px;")
        btn_cancel.clicked.connect(self.reject)

        self.btn_ok = QPushButton("Lanjutkan")
        self.btn_ok.setStyleSheet(
            "background:#3D8EF0; color:#fff; font-weight:700; padding:8px 16px; border-radius:6px;"
        )
        self.btn_ok.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_ok.clicked.connect(self._confirm)

        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(self.btn_ok)
        root.addLayout(btn_row)

    def _browse(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Pilih Model YOLO", "", "Model Files (*.pt *.onnx)"
        )
        if file_path:
            self.model_path = file_path
            self.lbl_path.setText(os.path.basename(file_path))
            self.lbl_path.setStyleSheet("color:#e2e2e9; font-size:12px;")

    def _confirm(self):
        if self.model_path:
            self.accept()
        else:
            QMessageBox.warning(
                self,
                "Model Belum Dipilih",
                "Upload model YOLO terlebih dahulu.\n\n"
                "Klik 'Browse File...' untuk memilih file model (.pt atau .onnx)."
            )
