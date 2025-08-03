from flask import (
    Flask,
    send_from_directory,
    abort,
    render_template,
    request,
    redirect,
    url_for,
    session,
)
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import date

from app.db import engine, Base
from app.models import VPS, User
from app.utils import calculate_remaining, generate_svg

app = Flask(__name__)
app.secret_key = "change-me"
Base.metadata.create_all(bind=engine)


def get_current_user():
    user_id = session.get("user_id")
    if user_id:
        with Session(engine) as db:
            return db.get(User, user_id)
    return None


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user or not user.is_admin:
            abort(403)
        return f(*args, **kwargs)

    return decorated


@app.context_processor
def inject_user():
    return {"current_user": get_current_user()}


def init_sample():
    with Session(engine) as db:
        if db.query(VPS).count() == 0:
            sample = VPS(
                name="demo",
                purchase_date=date.today(),
                renewal_days=30,
                price=10.0,
                renewal_price=10.0,
            )
            db.add(sample)
            db.commit()


init_sample()


def refresh_images():
    with Session(engine) as db:
        vps_list = db.query(VPS).all()
        for vps in vps_list:
            data = calculate_remaining(vps)
            generate_svg(vps, data)


scheduler = BackgroundScheduler(timezone="UTC")
scheduler.add_job(refresh_images, "cron", hour=0, minute=0)
scheduler.start()


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        with Session(engine) as db:
            if db.query(User).filter(User.username == username).first():
                return "User already exists", 400
            is_admin = db.query(User).count() == 0
            user = User(
                username=username,
                password_hash=generate_password_hash(password),
                is_admin=is_admin,
            )
            db.add(user)
            db.commit()
            session["user_id"] = user.id
        return redirect(url_for("index"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        with Session(engine) as db:
            user = db.query(User).filter(User.username == username).first()
            if not user or not check_password_hash(user.password_hash, password):
                return "Invalid credentials", 400
            session["user_id"] = user.id
        return redirect(url_for("index"))
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/admin/users", methods=["GET", "POST"])
@admin_required
def manage_users():
    with Session(engine) as db:
        if request.method == "POST":
            action = request.form.get("action")
            user_id = int(request.form.get("user_id"))
            user = db.get(User, user_id)
            if user:
                if action == "delete":
                    db.delete(user)
                    db.commit()
                elif action == "toggle_admin":
                    user.is_admin = not user.is_admin
                    db.commit()
        users = db.query(User).all()
    return render_template("admin_users.html", users=users)


@app.route("/")
def index():
    with Session(engine) as db:
        vps_list = db.query(VPS).all()
    return render_template("index.html", vps_list=vps_list)


@app.route("/vps/<string:name>.svg")
def get_vps_image(name: str):
    with Session(engine) as db:
        vps = db.query(VPS).filter(VPS.name == name).first()
        if not vps:
            abort(404)
        data = calculate_remaining(vps)
        svg_path = generate_svg(vps, data)
        directory = svg_path.parent
        return send_from_directory(directory, svg_path.name, mimetype="image/svg+xml")


if __name__ == "__main__":
    refresh_images()
    app.run(host="0.0.0.0", port=8280)
