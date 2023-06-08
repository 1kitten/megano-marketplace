# Payment-Service 💵

Сервис, позволяющий с легкостью оплачивать необходимые заказы!

### ⚙️ Установка

Собираем и запускаем проект через <a style="color: #72bcd4" href="https://www.docker.com/">docker-compose</a>:
```bash
docker compose build
docker compose up
```

### 🤔 Работа с платёжной системой

После запуска проекта, по адресу <code> http://0.0.0.0:5000/docs </code> будет доступна OpenAPI документация<br> с возможность тестирования эндпоинтов веб-приложения.

###### 🔗 Endpoints:

* <b style="color: #72bcd4"> /api/v1/purchase/ </b> - эндпоинт для проведения оплаты заказа пользователя. <br>После успешной оплаты, платёжная информация пользователя будет записана в MongoDB.

### 🛠️ Stack:


![Tools used](https://skillicons.dev/icons?i=py,fastapi,mongodb)