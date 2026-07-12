# Тестовое задание: 1С → Kafka → PostgreSQL

Рабочий демонстрационный контур: справочники 1С публикуются через HTTP API,
producer отправляет события в Kafka, а consumer сохраняет состояние в PostgreSQL.

```text
1С HTTP API → integration-service → Kafka → consumer-service → PostgreSQL
```

1С запущена на Windows вне Docker. Остальная инфраструктура описана в
`docker-compose.yml`.

