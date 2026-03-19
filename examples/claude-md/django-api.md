# Django REST API — Claude Code Instructions

## Stack
- Django 5.x, Django REST Framework, Python 3.12+
- PostgreSQL, Redis (cache + Celery broker)
- Celery (async tasks), Celery Beat (scheduled)
- Docker Compose (dev), AWS ECS (prod)

## Conventions
- Apps in `apps/` directory: `apps/users/`, `apps/orders/`, etc.
- ViewSets > APIViews for CRUD endpoints
- Serializers: separate `CreateSerializer`, `UpdateSerializer`, `ListSerializer`
- Signals for side effects, never in views
- Management commands for data operations

## Database
- Always create migrations with descriptive names: `python manage.py makemigrations --name describe_change`
- Never edit auto-generated migrations manually
- Use `django-extensions` `show_urls` to verify routing
- Indexes: add `db_index=True` on any field used in `filter()` or `order_by()`

## Testing
- pytest + pytest-django, factories with factory_boy
- Test files: `tests/test_<module>.py` in each app
- Use `@pytest.mark.django_db` for database tests
- Test API endpoints with `APIClient`, not direct view calls

## Celery
- Tasks in `apps/<app>/tasks.py`
- Always use `@shared_task(bind=True, max_retries=3)`
- Idempotent tasks: same input, same result, safe to retry
