FROM python:3.12-slim

WORKDIR /service
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/service
COPY consumer-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY consumer-service/app ./app
COPY tests/consumer_service ./tests
CMD ["python", "-m", "app.consumer"]
