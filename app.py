from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Секретный ключ нужен, чтобы работали session и flash.
# Для учебного проекта хватит строки, в реальном проекте ключ хранят в .env
app.config["SECRET_KEY"] = "change-this-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ---------- Модели (таблицы БД) ----------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)  # храним хеш, а не пароль
    tasks = db.relationship("Task", backref="user", lazy=True)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    done = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)


# ---------- Декоратор: проверка, что пользователь вошёл ----------

def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("Сначала войдите в аккаунт", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped_view


# ---------- Маршруты ----------

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    user_id = session["user_id"]

    # POST - пользователь отправил форму добавления задачи
    if request.method == "POST":
        title = request.form.get("title", "").strip()

        if not title:
            flash("Название задачи не может быть пустым", "error")
        elif len(title) > 200:
            flash("Название слишком длинное (максимум 200 символов)", "error")
        else:
            task = Task(title=title, user_id=user_id)
            db.session.add(task)
            db.session.commit()
            flash("Задача добавлена", "success")

        # Редирект после POST, чтобы при обновлении страницы форма не отправлялась повторно
        return redirect(url_for("index"))

    # GET - показываем только задачи текущего пользователя
    tasks = Task.query.filter_by(user_id=user_id).order_by(Task.id.desc()).all()
    return render_template("index.html", tasks=tasks)


@app.route("/toggle/<int:task_id>", methods=["POST"])
@login_required
def toggle(task_id):
    # Ищем задачу только среди задач текущего пользователя, чужую изменить нельзя
    task = Task.query.filter_by(id=task_id, user_id=session["user_id"]).first_or_404()
    task.done = not task.done
    db.session.commit()
    return redirect(url_for("index"))


@app.route("/delete/<int:task_id>", methods=["POST"])
@login_required
def delete(task_id):
    task = Task.query.filter_by(id=task_id, user_id=session["user_id"]).first_or_404()
    db.session.delete(task)
    db.session.commit()
    flash("Задача удалена", "success")
    return redirect(url_for("index"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        if not username or not password:
            flash("Заполните все поля", "error")
        elif len(password) < 6:
            flash("Пароль должен быть не короче 6 символов", "error")
        elif password != confirm:
            flash("Пароли не совпадают", "error")
        elif User.query.filter_by(username=username).first():
            # Проверка на существование пользователя
            flash("Пользователь с таким именем уже существует", "error")
        else:
            # Пароль в базу кладём только в виде хеша
            user = User(username=username, password_hash=generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
            flash("Регистрация прошла успешно, теперь войдите", "success")
            return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()

        # Сравниваем введённый пароль с хешем из базы
        if user and check_password_hash(user.password_hash, password):
            session.clear()
            session["user_id"] = user.id
            session["username"] = user.username
            flash("Вы вошли в аккаунт", "success")
            return redirect(url_for("index"))

        # Одно сообщение на оба случая, чтобы не подсказывать, какие логины существуют
        flash("Неверное имя пользователя или пароль", "error")

    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()  # удаляем все данные сессии
    flash("Вы вышли из аккаунта", "success")
    return redirect(url_for("login"))


# Команда для создания таблиц: flask --app app init-db
@app.cli.command("init-db")
def init_db():
    db.create_all()
    print("База данных создана")


if __name__ == "__main__":
    app.run(debug=True)