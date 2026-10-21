# Todo App

Учебное веб-приложение «Список задач» на Flask. Дисциплина «Python on web».

## Возможности
- регистрация и вход (пароли хранятся в виде хеша)
- у каждого пользователя свой список задач
- добавление, отметка выполнения и удаление задач
- flash-сообщения об ошибках и успехе

## Технологии
Python, Flask, Flask-SQLAlchemy, SQLite, Jinja2

## Запуск

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux / macOS
pip install -r requirements.txt
flask --app app init-db
flask --app app run --debug
```

Приложение откроется на http://127.0.0.1:5000