import os
import time
import datetime
from collections import Counter as PyCounter

import cv2
import numpy as np

from PyQt6.QtCore import QThread, pyqtSignal


class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)
    finished_signal      = pyqtSignal()
    count_updated_signal = pyqtSignal(int)
    log_updated_signal   = pyqtSignal(str, str, str, str)
    fps_updated_signal   = pyqtSignal(int)

    def __init__(self, source, region_points: list, model_path: str):
        super().__init__()
        self._source_raw   = source
        self.region_points = region_points
        self.model_path    = model_path
        self.source        = self._resolve_source(source)
        self.running       = True
        self.is_detecting  = False
        self.counter       = None
        self.yolo_model    = None
        self.last_total    = 0
        self.last_classwise_count = {}
        self.last_seen_class = "Unknown Object"
        self.frame_count = 0
        self.fps_history = []

    # ── Source resolution ────────────────────────────────────────────
    @staticmethod
    def _resolve_source(source):
        if source == "Webcam":
            return 0
        try:
            return int(source)
        except (ValueError, TypeError):
            return source

    def run(self):
        self._init_models()

        if self.source == 0:
            if os.name == 'nt':
                cap = cv2.VideoCapture(self.source, cv2.CAP_DSHOW)
            else:
                cap = cv2.VideoCapture(self.source)
            # Mengurangi buffer agar frame dari webcam tidak mengantre (mencegah delay)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            # Menurunkan resolusi kamera ke 640x480 agar beban komputasi YOLO lebih ringan
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        else:
            cap = cv2.VideoCapture(self.source)

        if not cap.isOpened():
            self.finished_signal.emit()
            return

        fps = cap.get(cv2.CAP_PROP_FPS)
        delay_ms = int(1000 / fps) if fps and fps > 0 else 33

        prev_time = time.time()

        while self.running:
            loop_start = time.time()
            ret, frame = cap.read()
            if not ret:
                if isinstance(self.source, str) and os.path.isfile(self.source):
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                break

            if self.is_detecting and self.counter:
                frame = self._process_frame(frame)

            self.change_pixmap_signal.emit(frame)
            
            curr_time = time.time()
            fps_val = int(1.0 / (curr_time - prev_time)) if (curr_time - prev_time) > 0 else 0
            prev_time = curr_time
            
            self.fps_history.append(fps_val)
            if len(self.fps_history) > 10:
                self.fps_history.pop(0)
            avg_fps = sum(self.fps_history) // len(self.fps_history)
            
            self.fps_updated_signal.emit(avg_fps)
            
            elapsed = int((curr_time - loop_start) * 1000)
            sleep_time = max(1, delay_ms - elapsed)
            QThread.msleep(sleep_time)

        cap.release()
        self.finished_signal.emit()

    # ── Model initialisation ─────────────────────────────────────────
    def _init_models(self):
        try:
            from ultralytics import solutions
            self.counter = solutions.ObjectCounter(
                region=self.region_points,
                show_out=False,
                show_in=False,
                model=self.model_path,
                conf=0.5,
                tracker="botsort.yaml",
            )
            self.yolo_model = None  # Dihapus agar tidak melakukan inisialisasi ganda model
        except Exception as e:
            print(f"[VideoThread] Model init error: {e}")

    # ── Frame processing ─────────────────────────────────────────────
    def _process_frame(self, frame: np.ndarray) -> np.ndarray:
        try:
            display = self._run_counter(frame)
            self._handle_detection(frame)
            return display
        except Exception as e:
            print(f"[VideoThread] Frame processing error: {e}")
            return frame

    def _run_counter(self, frame: np.ndarray) -> np.ndarray:
        try:
            results = self.counter(frame)
            try:
                return results.plot_im
            except AttributeError:
                return results[0].plot() if isinstance(results, list) else frame
        except TypeError:
            return self.counter.count(frame)

    def _get_class_from_counter(self) -> str:
        """Read the most recently tracked class name directly from the ObjectCounter.
        This avoids the timing mismatch of running a separate YOLO inference."""
        try:
            # ultralytics ObjectCounter stores tracker results in self.counter.track_history
            # or we can read from the last boxes processed by the counter's internal model.
            model = getattr(self.counter, "model", None)
            if model is None:
                return "Unknown Object"

            # The counter's internal predictor stores the last result
            predictor = getattr(model, "predictor", None)
            if predictor is None:
                return "Unknown Object"

            results = getattr(predictor, "results", None)
            if not results:
                return "Unknown Object"

            last_result = results[0]
            if not hasattr(last_result, "boxes") or last_result.boxes is None or len(last_result.boxes) == 0:
                return "Unknown Object"

            detected = []
            names = model.names
            for box in last_result.boxes:
                try:
                    cls_id = int(box.cls[0])
                    detected.append(names[cls_id])
                except Exception:
                    pass

            if detected:
                return PyCounter(detected).most_common(1)[0][0]
        except Exception as e:
            print(f"[VideoThread] Counter class extraction error: {e}")
        return "Unknown Object"

    def _update_class_from_frame(self, frame: np.ndarray):
        """Use secondary YOLO model to determine most common visible class."""
        if not self.yolo_model:
            return
        try:
            yolo_results = self.yolo_model(frame, verbose=False)
            result = yolo_results[0]
            if hasattr(result, "boxes") and result.boxes is not None and len(result.boxes) > 0:
                detected = []
                for box in result.boxes:
                    try:
                        cls_id = int(box.cls[0])
                        detected.append(self.yolo_model.names[cls_id])
                    except Exception:
                        pass
                if detected:
                    self.last_seen_class = PyCounter(detected).most_common(1)[0][0]
        except Exception as e:
            print(f"[VideoThread] Class extraction error: {e}")

    def _handle_detection(self, frame: np.ndarray):
        """Emit log and count signals when new objects cross the line."""
        total      = getattr(self.counter, "in_count", 0)
        increments = total - self.last_total

        if increments > 0:
            current_classwise = getattr(self.counter, "classwise_count", {})
            logged_something = False

            # Cek kelas mana yang jumlah IN-nya bertambah
            for cls_name, counts in current_classwise.items():
                current_in = counts.get('IN', 0)
                last_in = self.last_classwise_count.get(cls_name, 0)
                diff = current_in - last_in
                
                if diff > 0:
                    self.last_seen_class = cls_name
                    self.last_classwise_count[cls_name] = current_in
                    logged_something = True
                    
                    time_str = datetime.datetime.now().strftime("%H:%M:%S")
                    icon  = f"[{cls_name[0].upper()}]"
                    title = cls_name.capitalize()
                    
                    # Log sebanyak objek yang lewat dari kelas ini
                    for _ in range(diff):
                        self.log_updated_signal.emit(icon, title, "Logged", time_str)

            # Fallback jika classwise_count gagal mendeteksi
            if not logged_something:
                class_name = self._get_class_from_counter()
                if class_name == "Unknown Object":
                    self._update_class_from_frame(frame)
                    class_name = self.last_seen_class
                else:
                    self.last_seen_class = class_name

                time_str = datetime.datetime.now().strftime("%H:%M:%S")
                icon  = f"[{class_name[0].upper()}]" if class_name != "Unknown Object" else "[?]"
                title = class_name.capitalize() if class_name != "Unknown Object" else "Unknown Object"

                for _ in range(increments):
                    self.log_updated_signal.emit(icon, title, "Logged", time_str)

            self.last_total = total

        self.count_updated_signal.emit(total)

    def stop(self):
        self.running = False
        self.wait()
