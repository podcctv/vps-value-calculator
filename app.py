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
from datetime import date, timedelta

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
                transaction_date=date.today(),
                expiry_date=date.today() + timedelta(days=30),
                renewal_days=30,
                renewal_price=10.0,
                currency="USD",
                exchange_rate=1.0,
            )
            db.add(sample)
            db.commit()


init_sample()


def refresh_images():
    with Session(engine) as db:
        vps_list = db.query(VPS).all()
        for vps in vps_list:
            if not vps.dynamic_svg:
                continue
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


@app.route("/vps/new", methods=["GET", "POST"])
@login_required
def add_vps():
    if request.method == "POST":
        form = request.form
        with Session(engine) as db:
            vps = VPS(
                name=form["name"],
                transaction_date=date.fromisoformat(form["transaction_date"]),
                cycle_base_date=date.fromisoformat(form["cycle_base_date"]) if form.get("cycle_base_date") else None,
                expiry_date=date.fromisoformat(form["expiry_date"]) if form.get("expiry_date") else None,
                renewal_days=int(form.get("renewal_days") or 0),
                renewal_price=float(form.get("renewal_price") or 0.0),
                currency=form["currency"],
                exchange_rate=float(form.get("exchange_rate") or 1.0),
                vendor_name=form.get("vendor_name"),
                instance_config=form.get("instance_config"),
                location=form.get("location"),
                description=form.get("description"),
                traffic_limit=form.get("traffic_limit"),
                ip_address=form.get("ip_address"),
                payment_method=form.get("payment_method"),
                transaction_fee=float(form.get("transaction_fee") or 0.0),
                exchange_rate_source=form.get("exchange_rate_source"),
                update_cycle=int(form.get("update_cycle") or 7),
                dynamic_svg=bool(form.get("dynamic_svg")),
                status=form.get("status"),
            )
            db.add(vps)
            db.commit()
            data = calculate_remaining(vps)
            generate_svg(vps, data)
        return redirect(url_for("index"))
    return render_template("add_vps.html")


@app.route("/manage")
@login_required
def manage_vps():
    with Session(engine) as db:
        vps_list = db.query(VPS).all()
    return render_template("manage_vps.html", vps_list=vps_list)


@app.route("/vps/<int:vps_id>/edit", methods=["GET", "POST"])
@login_required
def edit_vps(vps_id: int):
    with Session(engine) as db:
        vps = db.get(VPS, vps_id)
        if not vps:
            abort(404)
        if request.method == "POST":
            form = request.form
            vps.name = form["name"]
            vps.transaction_date = date.fromisoformat(form["transaction_date"])
            vps.cycle_base_date = date.fromisoformat(form["cycle_base_date"]) if form.get("cycle_base_date") else None
            vps.expiry_date = date.fromisoformat(form["expiry_date"]) if form["expiry_date"] else None
            vps.renewal_days = int(form["renewal_days"] or 0)
            vps.renewal_price = float(form["renewal_price"] or 0.0)
            vps.currency = form["currency"]
            vps.exchange_rate = float(form["exchange_rate"] or 1.0)
            vps.vendor_name = form.get("vendor_name")
            vps.instance_config = form.get("instance_config")
            vps.location = form.get("location")
            vps.description = form.get("description")
            vps.traffic_limit = form.get("traffic_limit")
            vps.ip_address = form.get("ip_address")
            vps.payment_method = form.get("payment_method")
            vps.transaction_fee = float(form.get("transaction_fee") or 0.0)
            vps.exchange_rate_source = form.get("exchange_rate_source")
            vps.update_cycle = int(form.get("update_cycle") or 7)
            vps.dynamic_svg = bool(form.get("dynamic_svg"))
            vps.status = form.get("status")
            db.commit()
            data = calculate_remaining(vps)
            generate_svg(vps, data)
            return redirect(url_for("manage_vps"))
        vps_data = {
            "name": vps.name,
            "transaction_date": vps.transaction_date.isoformat(),
            "cycle_base_date": vps.cycle_base_date.isoformat() if vps.cycle_base_date else "",
            "expiry_date": vps.expiry_date.isoformat() if vps.expiry_date else "",
            "renewal_days": vps.renewal_days,
            "renewal_price": vps.renewal_price,
            "currency": vps.currency,
            "exchange_rate": vps.exchange_rate,
            "vendor_name": vps.vendor_name,
            "instance_config": vps.instance_config,
            "location": vps.location,
            "description": vps.description,
            "traffic_limit": vps.traffic_limit,
            "ip_address": vps.ip_address,
            "payment_method": vps.payment_method,
            "transaction_fee": vps.transaction_fee,
            "exchange_rate_source": vps.exchange_rate_source,
            "dynamic_svg": vps.dynamic_svg,
            "status": vps.status,
            "update_cycle": vps.update_cycle,
        }
        return render_template("add_vps.html", vps_data=vps_data)


@app.route("/vps/<int:vps_id>/delete", methods=["POST"])
@login_required
def delete_vps(vps_id: int):
    with Session(engine) as db:
        vps = db.get(VPS, vps_id)
        if vps:
            db.delete(vps)
            db.commit()
    return redirect(url_for("manage_vps"))


@app.route("/")
def index():
    return redirect(url_for("vps_list"))


@app.route("/vps")
def vps_list():
    with Session(engine) as db:
        vps_list = db.query(VPS).all()
        vps_data = [(vps, calculate_remaining(vps)) for vps in vps_list]
    return render_template("vps.html", vps_data=vps_data)


@app.route("/vps/<string:name>")
def view_vps(name: str):
    with Session(engine) as db:
        vps = db.query(VPS).filter(VPS.name == name).first()
        if not vps or not vps.dynamic_svg:
            abort(404)
    svg_url = url_for("get_vps_image", name=name)
    svg_abs_url = url_for("get_vps_image", name=name, _external=True)
    return render_template(
        "view_svg.html", name=name, svg_url=svg_url, svg_abs_url=svg_abs_url, vps_id=vps.id
    )


@app.route("/vps/<string:name>.svg")
def get_vps_image(name: str):
    with Session(engine) as db:
        vps = db.query(VPS).filter(VPS.name == name).first()
        if not vps or not vps.dynamic_svg:
            abort(404)
        data = calculate_remaining(vps)
        svg_path = generate_svg(vps, data)
        directory = svg_path.parent
        return send_from_directory(directory, svg_path.name, mimetype="image/svg+xml")


if __name__ == "__main__":
    refresh_images()
    app.run(host="0.0.0.0", port=8280)
