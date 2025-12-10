FROM python:3.11-slim

WORKDIR /app

COPY sensor_simulator/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY sensor_simulator /app/sensor_simulator

CMD ["python", "-m", "sensor_simulator"]