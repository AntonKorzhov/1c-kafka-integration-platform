# Подготовка 1С

В каталоге `1c/` находится готовый экспорт информационной базы:

```text
configuration.dt
```

Конфигурация уже содержит:

- справочник **Формы собственности**;
- справочник **Контрагенты**;
- HTTP-сервис интеграции;
- необходимые BSL-модули;
- демонстрационные данные.

1С запускается вне Docker. Остальная инфраструктура (Kafka, PostgreSQL,
integration-service, consumer-service и вспомогательные сервисы) поднимается
через Docker Compose.

---

# Восстановление информационной базы

1. Установить платформу **1С:Предприятие 8.3**.
2. Создать новую файловую информационную базу.
3. Открыть её в режиме **Конфигуратор**.
4. Выполнить:

```
Администрирование
→ Загрузить информационную базу...
```

5. Выбрать файл

```
1c/configuration.dt
```

После загрузки база полностью готова к использованию.

---

# Публикация HTTP-сервиса

Опубликуйте информационную базу на Apache/XAMPP (или IIS).

После публикации должны быть доступны следующие endpoint:

```
GET /InfoBase/hs/integration/forms-ownership
GET /InfoBase/hs/integration/counterparties
GET /InfoBase/hs/integration/counterparties?changed_since=<RFC3339 UTC>
```

Для Windows и Docker Desktop настройки по умолчанию уже соответствуют файлу
`.env`:

```dotenv
ONE_C_BASE_URL=http://host.docker.internal/InfoBase/hs/integration
ONE_C_HOST_HEADER=localhost
```

Если публикация использует другой адрес или виртуальный каталог, необходимо
изменить только параметр `ONE_C_BASE_URL`.

---

# Используемые справочники

## Формы собственности

Каждый элемент содержит:

- id
- code
- name
- deleted
- updated_at

Пример:

```json
{
  "id": "7d6874d2-86db-4ed1-b4ad-68839dc32901",
  "code": "000001",
  "name": "ООО",
  "deleted": false,
  "updated_at": "2026-07-11T09:20:00Z"
}
```

---

## Контрагенты

Каждый элемент содержит:

- id
- code
- name
- inn
- kpp
- ownership_form_id
- deleted
- updated_at

Пример:

```json
{
  "id": "b7e2a1f0-3b5d-4a1d-8d5a-1d6c8c1a0001",
  "code": "000001",
  "name": "ООО Ромашка",
  "inn": "7701234567",
  "kpp": "770101001",
  "ownership_form_id": "7d6874d2-86db-4ed1-b4ad-68839dc32901",
  "deleted": false,
  "updated_at": "2026-07-11T09:20:00Z"
}
```

Поле `id` содержит UUID объекта 1С.

Поле `ownership_form_id` содержит UUID связанной формы собственности и
используется consumer-service для заполнения внешнего ключа PostgreSQL.

---

# Проверка HTTP API

После публикации убедитесь, что сервис отвечает корректно.

### Bash

```bash
curl -i http://localhost/InfoBase/hs/integration/forms-ownership

curl -i http://localhost/InfoBase/hs/integration/counterparties

curl -i 'http://localhost/InfoBase/hs/integration/counterparties?changed_since=bad'
```
### PowerShell:

```powershell
Invoke-RestMethod http://localhost/InfoBase/hs/integration/forms-ownership

Invoke-RestMethod http://localhost/InfoBase/hs/integration/counterparties

Invoke-WebRequest `
'http://localhost/InfoBase/hs/integration/counterparties?changed_since=bad' `
-SkipHttpErrorCheck
```

Ожидаемый результат:

- первые два запроса возвращают HTTP 200;
- тело ответа содержит JSON-массив;
- запрос с некорректным `changed_since` возвращает HTTP 400.

---

# Содержимое каталога 1c

Полный экспорт информационной базы:

```text
configuration.dt
```

Скриншоты конфигурации, HTTP-сервиса и тестовых данных:

```text
screenshots/
```