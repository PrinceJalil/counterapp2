from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPen, QColor


class DrawingLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.drawing      = False
        self.line_done    = False
        self.start_point  = None
        self.end_point    = None
        self.current_point = None

    # ── Public ──────────────────────────────────────────────────────
    def reset_line(self):
        self.drawing       = False
        self.line_done     = False
        self.start_point   = None
        self.end_point     = None
        self.current_point = None
        self.update()

    # ── Mouse events ────────────────────────────────────────────────
    def mousePressEvent(self, event):
        if self.line_done:
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self.drawing       = True
            self.start_point   = event.pos()
            self.current_point = event.pos()

    def mouseMoveEvent(self, event):
        if self.drawing and not self.line_done:
            self.current_point = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.drawing:
            self.drawing   = False
            self.line_done = True
            self.end_point = event.pos()
            self.update()

    # ── Paint ────────────────────────────────────────────────────────
    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.start_point:
            return

        painter = QPainter(self)
        pen = QPen(QColor("#7a0167"), 2)
        painter.setPen(pen)

        p1 = self.start_point
        p2 = self.current_point if not self.line_done else self.end_point

        if p2:
            painter.drawLine(p1, p2)
            painter.setBrush(QColor("#7a0167"))
            painter.drawEllipse(p1, 5, 5)
            painter.drawEllipse(p2, 5, 5)
