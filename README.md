# Hot Feed Service

Django-сервис для hot feed с кэшированием и защитой от thundering herd.

**Задача B:** Hot Feed with Cache-Aside & Stampede Guard

## Быстрый старт

```bash
# Запуск всех сервисов (PostgreSQL + Redis + Django)
docker compose up --build

# Приложение доступно на http://localhost:8000
```

## API

### Hot Feed

```bash
GET /v1/feed/hot?limit=50
```

**Response**
```json
{
  "posts": [
    {
      "id": 1,
      "like_count": 150,
      "score": 45,
      "created_at": "2025-10-24T12:00:00Z"
    }
  ]
}
```

### Post CRUD

| Method | Endpoint | Описание |
| --- | --- | --- |
| `POST` | `/v1/feed/posts/` | создать пост |
| `GET` | `/v1/feed/posts/{id}/` | получить пост |
| `PUT/PATCH` | `/v1/feed/posts/{id}/update/` | обновить пост |
| `DELETE` | `/v1/feed/posts/{id}/delete/` | удалить пост |
| `GET` | `/v1/feed/posts/{id}/aggregates/` | агрегаты поста |

### Like Operations

| Method | Endpoint | Описание |
| --- | --- | --- |
| `POST` | `/v1/feed/posts/{post_id}/likes/` | поставить лайк `{ "user_id": 42 }` |
| `DELETE` | `/v1/feed/posts/{post_id}/likes/{user_id}/` | снять лайк |
| `GET` | `/v1/feed/posts/{post_id}/likes/{user_id}/status/` | статус лайка |


## Архитектура

### Слои приложения

```
Views (HTTP layer) → Services (Business logic) → Repositories (DB access) → Models
```

- `views.py` — HTTP-эндпоинты без бизнес-логики
- `services.py` — сценарии и транзакции
- `repositories.py` — доступ к БД, оптимизированные запросы
- `serializers.py`, `validators.py`, `exceptions.py` — вспомогательные слои
- `cache.py` + `signals.py` — cache-aside + инвалидация

### Ключевые решения

1. Денормализованный `like_count` и композитный индекс `(like_count DESC, created_at DESC)`
2. Score = лайки за последние 24 часа (через `annotate`)
3. Cache-aside на Redis с TTL=60s
4. Stampede guard через Redis `SETNX` + ожидание
5. Signals обновляют счётчики и инвалидируют популярные лимиты (10/20/50/100)
6. Like операции идемпотентны, используют `select_for_update`, `transaction.atomic`, `F()` выражения


## Тестирование

```bash
docker compose exec web python manage.py test feed.tests --keepdb

# Или через Makefile
make test

# Полная очистка БД (если нужно)
docker compose exec web python manage.py test feed.tests
```


## Команды

```bash
make build    # сборка Docker образов
make up       # запуск сервисов
make down     # остановка
make logs     # логи Django
make test     # полный запуск тестов
make shell    # Django shell
```
