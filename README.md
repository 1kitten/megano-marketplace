# MEGANO: Marketplace

## Запуск
Чтобы запустить работу, нужно ввести следующие команды:

```
cd marketplace
python manage.py runserver
```

## Запуск сервисов для работы с сервисом оплаты

Прежде всего необходимо запустить redis через docker командой:
```bash
docker run -d -p 6379:6379 redis
```

Далее запускаем celery командой:
```bash
celery -A marketplace worker -l info
```

Запускаем проект командой:
```bash
python manage.py runserver
```

**Инструкция по запуску сервиса оплаты находится в директории <code>app_payment/README.md</code>**


## Красивая админ-панель

Чтобы изменить дизайн админ-панели, необходимо загрузить фикстуру с темой командой:

```bash
python manage.py loaddata fixtures/admin_interface_theme_megano.json
```
