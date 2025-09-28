#Инструкция по запуску
Шаг 1: Запустите проект через Docker Compose
Откройте терминал и перейдите в каталог проекта.
Выполните:docker compose up -d
Шаг 2: Проверьте логи запуска
docker compose logs -f
Найдите строки об успешной загрузке приложения и инициализации БД.
Шаг 3: Доступ к API
Откройте браузер и перейдите по адресу:http://localhost:8000/docs для документации Swagger UIhttp://localhost:8000/redoc для 
##Методы:
POST /advertisement
GET /advertisement/{advertisement_id}
PATCH /advertisement/{advertisement_id}
DELETE /advertisement/{advertisement_id}
GET /advertisement
