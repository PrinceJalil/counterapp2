import json
import os
import shutil
from PyQt6.QtCore import QObject, QThread, QTimer, pyqtSignal
from PyQt6.QtWidgets import QDialog
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt

from core.video_thread import VideoThread
from database.database_worker import DatabaseWorker
from ui.dialogs.source_dialog import SourceDialog
from ui.dialogs.region_dialog import RegionDrawingDialog
from ui.dialogs.model_dialog import ModelUploadDialog
from widgets.log_item import LogItem


class AppController(QObject):
    send_db_batch = pyqtSignal(dict)

    def __init__(self, window):
        super().__init__()
        self._window      = window       # reference to MainWindow
        self.is_running   = False
        self.video_source = None
        self.region_points: list = []
        self.model_path   = ""
        self.thread: VideoThread | None = None
        self.temp_counts: dict = {}
        self.config_path = "app_config.json"

        self._load_config()
        self._setup_database()
        self._setup_batch_timer()

    def _load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    data = json.load(f)
                    self.video_source = data.get("video_source")
                    self.region_points = data.get("region_points", [])
                    self.model_path = data.get("model_path", "")
            except Exception as e:
                print(f"[Config] Error loading config: {e}")

    def _save_config(self):
        try:
            with open(self.config_path, "w") as f:
                json.dump({
                    "video_source": self.video_source,
                    "region_points": self.region_points,
                    "model_path": self.model_path
                }, f)
        except Exception as e:
            print(f"[Config] Error saving config: {e}")

    # ── Database setup ───────────────────────────────────────────────
    def _setup_database(self):
        self.db_thread = QThread()
        self.db_worker = DatabaseWorker(db_path="database/database.db")
        self.db_worker.moveToThread(self.db_thread)
        self.send_db_batch.connect(self.db_worker.save_batch_to_db)
        self.db_worker.status_msg.connect(lambda msg: print(f"[DB] {msg}"))
        self.db_worker.error_msg.connect(lambda msg: print(f"[DB ERR] {msg}"))
        self.db_thread.start()

    def _setup_batch_timer(self):
        self._batch_timer = QTimer()
        self._batch_timer.setInterval(3000)
        self._batch_timer.timeout.connect(self._flush_batch)
        self._batch_timer.start()

    def add_to_batch(self, class_name: str):
        self.temp_counts[class_name] = self.temp_counts.get(class_name, 0) + 1

    def _flush_batch(self):
        if self.temp_counts:
            self.send_db_batch.emit(dict(self.temp_counts))
            self.temp_counts.clear()

    # ── Toggle ───────────────────────────────────────────────────────
    def toggle(self):
        if self.is_running:
            self.stop()
        else:
            if self.video_source is not None and self.model_path:
                self.start()
            else:
                self._open_source_dialog()

    def reset_config(self):
        self.video_source = None
        self.region_points = []
        self.model_path = ""
        if os.path.exists(self.config_path):
            try:
                os.remove(self.config_path)
            except:
                pass

        source_dir = "source"
        if os.path.exists(source_dir):
            try:
                shutil.rmtree(source_dir)
            except Exception as e:
                print(f"[Config] Error removing source dir: {e}")

        self._window.on_state_changed(running=False)

    # ── Startup dialog flow ──────────────────────────────────────────
    def _open_source_dialog(self):
        src_dlg = SourceDialog(self._window)
        if src_dlg.exec() != QDialog.DialogCode.Accepted or src_dlg.chosen_source is None or src_dlg.chosen_source == "":
            return

        reg_dlg = RegionDrawingDialog(src_dlg.chosen_source, self._window)
        if reg_dlg.exec() != QDialog.DialogCode.Accepted or len(reg_dlg.region_points) != 2:
            return

        mod_dlg = ModelUploadDialog(self._window)
        if mod_dlg.exec() != QDialog.DialogCode.Accepted or not mod_dlg.model_path:
            return

        source_dir = "source"
        os.makedirs(source_dir, exist_ok=True)

        # Copy model
        model_filename = os.path.basename(mod_dlg.model_path)
        copied_model_path = os.path.join(source_dir, model_filename)
        try:
            shutil.copy2(mod_dlg.model_path, copied_model_path)
            self.model_path = copied_model_path
        except Exception as e:
            print(f"[Config] Error copying model: {e}")
            self.model_path = mod_dlg.model_path

        # Copy video if not webcam
        if isinstance(src_dlg.chosen_source, str):
            video_filename = os.path.basename(src_dlg.chosen_source)
            copied_video_path = os.path.join(source_dir, video_filename)
            try:
                shutil.copy2(src_dlg.chosen_source, copied_video_path)
                self.video_source = copied_video_path
            except Exception as e:
                print(f"[Config] Error copying video: {e}")
                self.video_source = src_dlg.chosen_source
        else:
            self.video_source = src_dlg.chosen_source

        self.region_points = reg_dlg.region_points
        self._save_config()
        self.start()

    # ── Start / Stop ─────────────────────────────────────────────────
    def start(self):
        self._start_video_thread()
        self.is_running = True
        self._window.on_state_changed(running=True,
                                      source=self.video_source,
                                      model=self.model_path)

    def stop(self):
        if self.thread:
            self.thread.stop()
            self.thread = None
        self.is_running   = False
        self._window.on_state_changed(running=False, source=self.video_source, model=self.model_path)

    # ── Video thread ─────────────────────────────────────────────────
    def _start_video_thread(self):
        if self.thread:
            self.thread.stop()

        self.thread = VideoThread(self.video_source, self.region_points, self.model_path)
        self.thread.change_pixmap_signal.connect(self._on_new_frame)
        self.thread.finished_signal.connect(self._on_feed_finished)
        self.thread.count_updated_signal.connect(self._window.on_count_updated)
        self.thread.log_updated_signal.connect(self._on_log_updated)
        self.thread.fps_updated_signal.connect(self._window.on_fps_updated)
        self.thread.is_detecting = True
        self.thread.start()

    def _on_new_frame(self, cv_img):
        h, w, ch = cv_img.shape
        if ch == 3:
            import cv2 as _cv2
            rgb = _cv2.cvtColor(cv_img, _cv2.COLOR_BGR2RGB)
            qt_img = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        else:
            qt_img = QImage(cv_img.data, w, h, w, QImage.Format.Format_Grayscale8)

        lbl = self._window.video_label
        if lbl.isVisible() and lbl.width() > 0:
            pixmap = QPixmap.fromImage(qt_img).scaled(
                lbl.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            lbl.setPixmap(pixmap)

    def _on_log_updated(self, icon: str, title: str, status: str, time_str: str):
        self.add_to_batch(title)
        self._window.on_log_entry(icon, title, status, time_str)

    def _on_feed_finished(self):
        if self.is_running:
            self.stop()

    # ── Cleanup ──────────────────────────────────────────────────────
    def shutdown(self):
        if self.thread:
            self.thread.stop()
        self._batch_timer.stop()
        if hasattr(self, "db_thread"):
            self.db_thread.quit()
            self.db_thread.wait()
