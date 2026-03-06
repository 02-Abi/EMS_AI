@echo off
cd C:\enterprise-ems
call venv\Scripts\activate
python manage.py run_ml_predictions
python manage.py detect_anomalies