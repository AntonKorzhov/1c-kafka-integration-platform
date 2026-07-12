# Тестовое задание: 1С → Kafka → PostgreSQL

Рабочий демонстрационный контур: справочники 1С публикуются через HTTP API,
producer отправляет события в Kafka, а consumer сохраняет состояние в PostgreSQL.

```text
1С HTTP API → integration-service → Kafka → consumer-service → PostgreSQL
```

1С запущена на Windows вне Docker. Остальная инфраструктура описана в
`docker-compose.yml`.


## Состав решения

- 1С: справочники «Формы собственности» и «Контрагенты», HTTP JSON API;
- Apache Kafka 3.8.1, single-node KRaft;
- PostgreSQL 16 с PK, FK и `INSERT ... ON CONFLICT DO UPDATE`;
- `integration-service`: full/incremental producer на Python;
- `consumer-service`: consumer group, retry, DLQ и PostgreSQL upsert;
- Kafka UI и pgAdmin в базовом запуске Compose;
- Дополнительно реализованы unit-тесты в `tests/`.# Тестовое задание: 1С → Kafka → PostgreSQL

Рабочий демонстрационный контур: справочники 1С публикуются через HTTP API,
producer отправляет события в Kafka, а consumer сохраняет состояние в PostgreSQL.

```text
1С HTTP API → integration-service → Kafka → consumer-service → PostgreSQL
```

1С запущена на Windows вне Docker. Остальная инфраструктура описана в
`docker-compose.yml`.

## Состав решения

- 1С: справочники «Формы собственности» и «Контрагенты», HTTP JSON API;
- Apache Kafka 3.8.1, single-node KRaft;
- PostgreSQL 16 с PK, FK и `INSERT ... ON CONFLICT DO UPDATE`;
- `integration-service`: full/incremental producer на Python;
- `consumer-service`: consumer group, retry, DLQ и PostgreSQL upsert;
- Kafka UI и pgAdmin в базовом запуске Compose;
- Дополнительно реализованы unit-тесты в `tests/`.

## Структура решения

```text
1c/                    Инструкция, BSL-модули, export и screenshots
consumer-service/      Kafka → PostgreSQL consumer
integration-service/   1С HTTP API → Kafka producer
migrations/            PostgreSQL DDL
docs/                  Архитектурные решения
sql/                   SQL-проверки результата
tests/                 pytest unit-тесты двух сервисов
```

## Архитектурные решения

Интеграция построена по событийной схеме: данные из 1С HTTP API передаются через integration-service в Kafka, далее обрабатываются consumer-service и сохраняются в PostgreSQL.

Основные архитектурные решения:
- событийное взаимодействие через Kafka;
- раздельные топики для справочников 1С;
- идемпотентная обработка сообщений;
- инкрементальная синхронизация через watermark;
- обработка ошибок через retry и Dead Letter Queue.

Подробное описание архитектуры и принятых решений:
[docs/architecture.md](docs/architecture.md)

## Требования

- Docker Desktop (Windows/macOS) или Docker Engine + Compose plugin (Linux);
- опубликованная база 1С с HTTP API;
- для Windows: 1С и Apache/XAMPP запущены на хосте.

Адреса API на Windows-хосте:

```text
http://localhost/InfoBase/hs/integration/forms-ownership
http://localhost/InfoBase/hs/integration/counterparties
```

Подробности настройки 1С и экспорта конфигурации: [1c/setup.md](1c/setup.md).

## Настройка `.env`

Создайте локальный файл настроек. Он содержит пароли и не должен попадать в Git.

### Bash

```bash
cp .env.example .env
```

### PowerShell

```powershell
Copy-Item .env.example .env
```

Далее измените в `.env` минимум следующие строки:

```dotenv
POSTGRES_PASSWORD=<ваш_пароль>
PGADMIN_DEFAULT_EMAIL=admin@example.local
PGADMIN_DEFAULT_PASSWORD=<пароль_pgadmin>
GF_SECURITY_ADMIN_USER=admin
GF_SECURITY_ADMIN_PASSWORD=<пароль_grafana>
```

Для Windows + Docker Desktop значения 1С уже подходят:

```dotenv
ONE_C_BASE_URL=http://host.docker.internal/InfoBase/hs/integration
ONE_C_HOST_HEADER=localhost
```

`host.docker.internal` — адрес Windows-хоста из контейнера; заголовок
`Host: localhost` нужен текущей публикации XAMPP. 

На Linux укажите адрес
вашего HTTP-сервера 1С в `ONE_C_BASE_URL`; при необходимости очистите
`ONE_C_HOST_HEADER`.

## Запуск всего контура

### PowerShell/Bash

```bash
docker compose up -d --build
docker compose ps
```

Ожидаются следующие обязательные сервисы: `postgres`, `kafka`, `integration-service`,
`consumer-service`, `kafka-ui`, `pgadmin`. 

`kafka-init` — одноразовый сервис, который создаёт топики и завершится с кодом `0`.

Дополнительные сервисы диагностики: `loki`, `alloy`, `grafana`.

## Основные интерфейсы и healthcheck

| Компонент | Адрес |
|---|---|
| Kafka UI | http://localhost:8082 |
| pgAdmin | http://localhost:5050 |
| integration-service health | http://localhost:8080/health |
| consumer-service health | http://localhost:8081/health |

В pgAdmin используйте учётные данные `PGADMIN_DEFAULT_EMAIL` и
`PGADMIN_DEFAULT_PASSWORD` из `.env`. 

После входа в pgAdmin произведите добавление PostgreSQL-сервера:

```text
Name: integration
Host name/address: postgres
Port: 5432
Maintenance database: integration
Username: integration
Password: значение POSTGRES_PASSWORD из .env
```
## Дополнительные интерфейсы

Для удобства диагностики в проект дополнительно включены Grafana, Loki и Alloy.

| Компонент | Адрес |
|---|---|
| Grafana logs | http://localhost:3000 |
| Grafana Alloy status | http://localhost:12345 |
| Loki API | http://localhost:3100/ready |

Данные компоненты не участвуют в основном потоке передачи данных
`1С → Kafka → PostgreSQL`, а используются для централизованного сбора,
хранения и просмотра логов всех сервисов Docker Compose.

Для входа в Grafana используйте `GF_SECURITY_ADMIN_USER` / `GF_SECURITY_ADMIN_PASSWORD`
из `.env`. 

Источники данных Loki и dashboard **Integration / 1С Integration — Logs**
создаются автоматически. Dashboard показывает stdout всех Compose-сервисов,
позволяет фильтровать по сервису и отдельно выводит JSON-записи уровней
`ERROR`, `WARNING`, `CRITICAL`.

Alloy обнаруживает контейнеры текущего Compose-проекта через Docker socket.
Для JSON-логов Python-сервисов поля `service` и `level` извлекаются в Loki
labels; текстовые логи Kafka/PostgreSQL также сохраняются и доступны по фильтру
`compose_service`.

## Синхронизация

### Полная синхронизация

#### PowerShell/Bash

```bash
docker compose run --rm integration-service python -m app.sync --mode full
```

### Инкрементальная синхронизация

После изменения записи в 1С или пометки на удаление:

#### PowerShell/Bash

```bash
docker compose run --rm integration-service python -m app.sync --mode incremental
```

Producer хранит watermark в таблице `sync_state`. Он намеренно повторно читает
одну предыдущую секунду watermark, чтобы не потерять изменения на границе
секунды; повторная доставка безопасна благодаря Kafka key и PostgreSQL upsert.

## Просмотр Kafka

Для просмотра Kafka есть два режима взаимодействия:
- через графический интерфейс Kafka UI (http://localhost:8082);
- через командную строку.

### Взаимодействие через командную строку

### PowerShell/Bash

```bash
docker compose exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --list

docker compose exec kafka /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server kafka:9092 --topic 1c.counterparties.v1 --from-beginning --property print.key=true --property key.separator=' | ' --timeout-ms 5000
```

Обязательные топики:

```text
1c.ownership_forms.v1
1c.counterparties.v1
1c.integration.dlq.v1
```

Пустой DLQ проверяется так же, только с `--topic 1c.integration.dlq.v1`.

## Просмотр PostgreSQL

Для просмотра PostgreSQL есть два режима взаимодействия:
- через графический интерфейс pgAdmin (http://localhost:5050);
- через командную строку.

### Взаимодействие через командную строку

### Bash

```bash
cat sql/checks.sql | docker compose exec -T postgres \
  psql -U integration -d integration
```

### PowerShell

```powershell
Get-Content sql/checks.sql |
  docker compose exec -T postgres psql -U integration -d integration
```

Проверка idempotency после повторного `full`:

### PowerShell/Bash

```bash
docker compose exec -T postgres psql -U integration -d integration -c "
SELECT 'ownership_forms' AS entity, count(*) AS rows, count(DISTINCT id) AS distinct_ids
FROM ownership_forms
UNION ALL
SELECT 'counterparties', count(*), count(DISTINCT id)
FROM counterparties;"
```

Ожидаемый результат после демонстрационной full-синхронизации: `5/5` и `8/8`.

## Логи и диагностика

Для просмотра логов и проведения диагностики есть два режима взаимодействия:
- через графический интерфейс Grafana (http://localhost:3000);
- через командную строку.

### Взаимодействие через командную строку

### PowerShell/Bash

```bash
docker compose logs --tail=100 consumer-service
docker compose logs --tail=100 integration-service
docker compose logs -f --tail=100
```

Лог full/incremental producer выводится непосредственно в консоль, потому что
он запускается как одноразовый контейнер. Сохранить его в файл можно так:

### Bash

```bash
docker compose run --rm integration-service python -m app.sync --mode full \
  2>&1 | tee sync-full.log
```

### PowerShell

```powershell
docker compose run --rm integration-service python -m app.sync --mode full `
  2>&1 | Tee-Object -FilePath .\sync-full.log
```

## Остановка и очистка

Остановка с сохранением PostgreSQL-данных:

```bash
docker compose down
```

Полный сброс Docker-данных **без затрагивания базы 1С**:

```bash
docker compose down -v
```

После `down -v` снова выполните `docker compose up -d --build`, затем full.

## Ограничения

Решение предназначено для реализации тестового задания: одна Kafka-нода, plaintext без
TLS/SASL, без OAuth/JWT, Kubernetes, Schema Registry, CDC/outbox и Prometheus.
В production нужны HA Kafka, секреты вне `.env`, TLS/SASL, схемы событий,
метрики, alerting и стратегия CDC/outbox.

## Автоматические тесты

Проект содержит unit-тесты для `integration-service` и `consumer-service`.
Они не требуют запуска 1С, Kafka или PostgreSQL и выполняются с использованием
mock-объектов и `monkeypatch`.

Проверяются:

- нормализация данных, полученных из HTTP API 1С;
- валидация UUID, временных меток RFC 3339 и nullable-полей;
- формирование Kafka-событий и стабильность Kafka key;
- логика инкрементальной синхронизации и обновления watermark;
- корректная обработка ошибок при публикации сообщений;
- валидация входящих Kafka-событий;
- маршрутизация событий consumer по `event_type`.

Всего выполняется 13 test cases: 9 для `integration-service` и 4 для
`consumer-service` (часть функций параметризована).

### PowerShell/Bash

```bash
docker compose build integration-service consumer-service
docker compose run --rm --no-deps integration-service pytest -q tests --junitxml=/test-results/integration-service.xml
docker compose run --rm --no-deps consumer-service pytest -q tests --junitxml=/test-results/consumer-service.xml
```

Для подробного результата замените `-q` на `-vv`. 

JUnit-отчёты сохраняются в каталог `test-results/`.

## Возможные улучшения

Для промышленной эксплуатации решение можно расширить следующим образом:

- развернуть отказоустойчивый Kafka-кластер вместо single-node;
- использовать TLS/SASL и внешнее хранилище секретов;
- перейти с периодического опроса 1С на CDC/Outbox Pattern либо механизм событий платформы;
- реализовать полноценные интеграционные тесты с Kafka и PostgreSQL;
- внедрить CI/CD с автоматическим запуском тестов, проверкой миграций и сборкой Docker-образов.