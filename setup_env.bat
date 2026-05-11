@echo off
echo ===================================================
echo   Setup Environment Project Counter App
echo ===================================================
echo.

echo [1/3] Membuat Virtual Environment...
python -m venv venv

echo.
echo [2/3] Mengaktifkan Virtual Environment...
call venv\Scripts\activate.bat

echo.
echo [3/3] Menginstall dependencies (mungkin membutuhkan waktu beberapa menit)...
pip install -r requirements.txt

echo.
echo ===================================================
echo   Setup Selesai!
echo   Environment siap digunakan.
echo   Untuk menjalankan aplikasi, jalankan: run_app.bat
echo ===================================================
pause
