.PHONY: up down logs sync-full sync-incremental topics psql test

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f --tail=100

sync-full:
	docker compose run --rm integration-service python -m app.sync --mode full

sync-incremental:
	docker compose run --rm integration-service python -m app.sync --mode incremental

topics:
	docker compose exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --list

psql:
	docker compose exec postgres psql -U integration -d integration

test:
	docker compose build integration-service consumer-service
	docker compose run --rm --no-deps integration-service pytest -q tests --junitxml=/test-results/integration-service.xml
	docker compose run --rm --no-deps consumer-service pytest -q tests --junitxml=/test-results/consumer-service.xml
