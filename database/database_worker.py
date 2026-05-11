import sqlite3
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

import datetime

class DatabaseWorker(QObject):
    status_msg = pyqtSignal(str)
    error_msg = pyqtSignal(str)

    def __init__(self, db_path="database/database.db"):
        super().__init__()
        self.db_path = db_path

    @pyqtSlot(dict)
    def save_batch_to_db(self, data_batch):
        if not data_batch:
            return

        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS history_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT (datetime('now', '+7 hours')),
                    class_name TEXT,
                    count_in INTEGER
                )
            ''')

            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            records = [(current_time, cls_name, count) for cls_name, count in data_batch.items()]

            cursor.executemany('''
                INSERT INTO history_logs (timestamp, class_name, count_in)
                VALUES (?, ?, ?)
            ''', records)

            conn.commit()
            
            self.status_msg.emit(f"Berhasil menyimpan {len(records)} baris data class secara batch.")

        except Exception as e:
            self.error_msg.emit(f"Database Error saat Batch Insert: {str(e)}")

        finally:
            if conn is not None:
                conn.close()
