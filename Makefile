.PHONY: build up down restart logs test shell migrate createsuperuser clean

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose restart

logs:
	docker compose logs -f web

logs-all:
	docker compose logs -f

test:
	docker compose exec web python manage.py test feed.tests

shell:
	docker compose exec web python manage.py shell

migrate:
	docker compose exec web python manage.py migrate

makemigrations:
	docker compose exec web python manage.py makemigrations

createsuperuser:
	docker compose exec web python manage.py createsuperuser

clean:
	docker compose down -v
	docker system prune -f

ps:
	docker compose ps

check:
	docker compose exec web python manage.py check

flake8:
	docker compose exec web flake8 feed/ hotfeed/ manage.py --max-line-length=88 --exclude=migrations

isort:
	docker compose exec web isort feed/ hotfeed/ manage.py

isort-check:
	docker compose exec web isort --check-only feed/ hotfeed/ manage.py
