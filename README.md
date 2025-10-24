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

```bash
# топ постов по лайкам за 24 часа
GET /v1/feed/hot?limit=50
```

**Ответ:**
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

## Тестирование

```bash
# Запуск всех тестов
docker compose exec web python manage.py test feed.tests

# Или через Makefile
make test
```

## Архитектура

### Модели

- **Post**: `id`, `like_count`, `created_at`
- **Like**: `id`, `post_id`, `user_id`, `created_at`

### Ключевые решения

1. **Денормализация** - `like_count` в Post для быстрой выборки
2. **Composite index** - `(like_count DESC, created_at DESC)` для hot feed
3. **Score** - количество лайков за последние 24 часа
4. **Cache-Aside** - Redis кэш с TTL=60s
5. **Stampede guard** - Distributed lock через Redis SETNX
6. **Auto-invalidation** - Django signals при создании/удалении Like


## Команды

```bash
make build    # Сборка Docker образов
make up       # Запуск сервисов
make down     # Остановка
make logs     # Просмотр логов
make test     # Запуск тестов
make shell    # Django shell
```
