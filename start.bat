@echo off

start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" ^
--remote-debugging-port=9222 ^
--user-data-dir="%~dp0chrome-profile" ^
"https://eticket.railway.gov.bd/"

timeout /t 3 /nobreak >nul

call "venv\Scripts\activate.bat"

python main.py

pause