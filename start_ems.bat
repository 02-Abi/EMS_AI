@echo off
echo ================================
echo    EMS Startup Script
echo ================================
cd C:\enterprise-ems
call venv\Scripts\activate
echo 🔥 Clearing all sessions...
python manage.py clearsessions
echo 🚀 Starting server...
echo.
echo IMPORTANT: Use Incognito Mode in browser!
echo URL: http://127.0.0.1:8000/
echo.
python manage.py runserver
pause