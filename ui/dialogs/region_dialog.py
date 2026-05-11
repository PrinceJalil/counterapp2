import cv2

from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap

from widgets.drawing_label import DrawingLabel


class RegionDrawingDialog(QDialog):
    def __init__(self, source, parent=None):
        super().__init__(parent)
        self.source        = source
        self.region_points = []
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(800, 600)

        self._orig_w = 0
        self._orig_h = 0
        self._first_frame_pixmap = self._get_first_frame()
        self._init_ui()

    # ── Frame capture ────────────────────────────────────────────────
    def _get_first_frame(self) -> QPixmap:
        cap = cv2.VideoCapture(self.source)
        if cap.isOpened():
            self._orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self._orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            ret, frame = cap.read()
            cap.release()
            if ret:
                h, w, ch = frame.shape
                if self._orig_w == 0: self._orig_w = w
                if self._orig_h == 0: self._orig_h = h
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
                return QPixmap.fromImage(img)

        pm = QPixmap(800, 500)
        pm.fill(Qt.GlobalColor.black)
        return pm

    # ── UI ───────────────────────────────────────────────────────────
    def _init_ui(self):
        outer = QWidget(self)
        outer.setObjectName("dialog-card")
        outer.setGeometry(0, 0, 800, 600)
        outer.setStyleSheet(
            "#dialog-card { background-color: #1a1b21; border: 1px solid #33353a; border-radius: 16px; }"
        )

        root = QVBoxLayout(outer)
        root.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Tentukan Counting Line")
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #e2e2e9;")
        root.addWidget(title)

        self.view_lbl = DrawingLabel()
        self.view_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.view_lbl.setStyleSheet("background-color: #000; border-radius: 8px;")

        scaled_pm = self._first_frame_pixmap.scaled(
            760, 480,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.view_lbl.setPixmap(scaled_pm)
        if not scaled_pm.isNull():
            self.view_lbl.setFixedSize(scaled_pm.size())

        view_container = QWidget()
        v_l = QHBoxLayout(view_container)
        v_l.setContentsMargins(0, 0, 0, 0)
        v_l.addWidget(self.view_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        root.addWidget(view_container, stretch=1)

        btn_row = QHBoxLayout()
        btn_reset = QPushButton("Reset Line")
        btn_reset.setStyleSheet("background:#282a2f; color:#8b919e; padding:8px 16px; border-radius:6px;")
        btn_reset.clicked.connect(self.view_lbl.reset_line)

        btn_save = QPushButton("Save")
        btn_save.setStyleSheet(
            "background:#3D8EF0; color:#fff; font-weight:bold; padding:8px 16px; border-radius:6px;"
        )
        btn_save.clicked.connect(self._save_region)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setStyleSheet("background:transparent; color:#8b919e; padding:8px 16px;")
        btn_cancel.clicked.connect(self.reject)

        btn_row.addWidget(btn_reset)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        root.addLayout(btn_row)

    # ── Save logic ───────────────────────────────────────────────────
    def _save_region(self):
        if not self.view_lbl.line_done or not self.view_lbl.start_point or not self.view_lbl.end_point:
            QMessageBox.warning(
                self,
                "Line Belum Ditentukan",
                "Tentukan counting line terlebih dahulu.\n\n"
                "Klik dan seret pada gambar untuk menggambar garis."
            )
            return

        sh = self.view_lbl.height()
        sw = self.view_lbl.width()
        orig_w = self._orig_w
        orig_h = self._orig_h

        if sh > 0 and sw > 0 and orig_w > 0 and orig_h > 0:
            scale_x = orig_w / sw
            scale_y = orig_h / sh
            x1 = int(self.view_lbl.start_point.x() * scale_x)
            y1 = int(self.view_lbl.start_point.y() * scale_y)
            x2 = int(self.view_lbl.end_point.x() * scale_x)
            y2 = int(self.view_lbl.end_point.y() * scale_y)
            self.region_points = [(x1, y1), (x2, y2)]
        else:
            self.region_points = [(0, 0), (0, 0)]

        self.accept()
