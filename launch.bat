@echo off
cd /d F:\SmartResume\smart-resume-hub\backend
start /min "SmartResume Backend" "F:\SmartResume\smart-resume-hub\backend\venv\Scripts\python.exe" manage.py runserver 127.0.0.1:8000
cd /d F:\SmartResume\smart-resume-hub\frontend
start /min "SmartResume Frontend" cmd /c "npm run dev"
