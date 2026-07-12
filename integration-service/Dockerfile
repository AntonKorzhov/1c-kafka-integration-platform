FROM python:3.12-slim

WORKDIR /service
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/service
COPY integration-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY integration-service/app ./app
COPY tests/integration_service ./tests
CMD ["python", "-m", "app.http_server"]
