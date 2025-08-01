@echo off

:: Lấy thư mục chứa file .bat
set "BATDIR=%~dp0"

:: Chuyển vào thư mục đó
cd /d "%BATDIR%"


:: Chạy script Python
python bootFOTA_APR.py

:: Giữ cửa sổ console để xem kết quả
pause

:: :loop
:: goto loop