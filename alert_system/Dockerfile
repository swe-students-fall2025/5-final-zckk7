FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY alert_engine.py .

CMD ["python", "-u", "alert_engine.py"]