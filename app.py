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
from app.models import VPS, User, InviteCode, SiteConfig
from app.utils import calculate_remaining, generate_svg, parse_instance_config

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
                renewal_price=10.0,
                currency="USD",
                exchange_rate=1.0,
            )
            db.add(sample)
        if db.query(InviteCode).count() == 0:
            db.add(InviteCode(code="Flanker"))
        if db.query(SiteConfig).count() == 0:
            db.add(SiteConfig(image_base_url="", noodseek_id="@Flanker"))
        db.commit()


init_sample()


def refresh_images():
    with Session(engine) as db:
        config = db.query(SiteConfig).first()
        vps_list = db.query(VPS).all()
        for vps in vps_list:
            if not vps.dynamic_svg:
                continue
            data = calculate_remaining(vps)
            generate_svg(vps, data, config)


scheduler = BackgroundScheduler(timezone="UTC")
scheduler.add_job(refresh_images, "cron", hour=0, minute=0)
scheduler.start()


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        invite = request.form.get("invite_code", "")
        with Session(engine) as db:
            if db.query(User).filter(User.username == username).first():
                return "User already exists", 400
            user_count = db.query(User).count()
            if user_count > 0:
                code_obj = db.query(InviteCode).first()
                if not code_obj or invite != code_obj.code:
                    return "Invalid invitation code", 400
            is_admin = user_count == 0
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
            if action == "set_invite_code":
                code = request.form.get("invite_code", "")
                obj = db.query(InviteCode).first()
                if obj:
                    obj.code = code
                else:
                    db.add(InviteCode(code=code))
                db.commit()
            elif action == "set_site_config":
                base_url = request.form.get("image_base_url", "")
                noodseek_id = request.form.get("noodseek_id", "")
                cfg = db.query(SiteConfig).first()
                if cfg:
                    cfg.image_base_url = base_url
                    cfg.noodseek_id = noodseek_id
                else:
                    db.add(SiteConfig(image_base_url=base_url, noodseek_id=noodseek_id))
                db.commit()
            else:
                user_id = int(request.form.get("user_id"))
                user = db.get(User, user_id)
                if user:
                    if action == "delete":
                        db.delete(user)
                    elif action == "toggle_admin":
                        user.is_admin = not user.is_admin
                    db.commit()
        users = db.query(User).all()
        invite_obj = db.query(InviteCode).first()
        invite_code = invite_obj.code if invite_obj else ""
        config = db.query(SiteConfig).first()
    return render_template(
        "admin_users.html", users=users, invite_code=invite_code, config=config
    )


@app.route("/vps/new", methods=["GET", "POST"])
@login_required
def add_vps():
    if request.method == "POST":
        form = request.form
        with Session(engine) as db:
            vps = VPS(
                name=form["name"],
                purchase_date=date.fromisoformat(form["purchase_date"]),
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
            config = db.query(SiteConfig).first()
            data = calculate_remaining(vps)
            generate_svg(vps, data, config)
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
            vps.purchase_date = date.fromisoformat(form["purchase_date"])
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
            config = db.query(SiteConfig).first()
            data = calculate_remaining(vps)
            generate_svg(vps, data, config)
            return redirect(url_for("manage_vps"))
        vps_data = {
            "name": vps.name,
            "purchase_date": vps.purchase_date.isoformat(),
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
        vps_data = []
        for vps in vps_list:
            data = calculate_remaining(vps)
            specs = parse_instance_config(vps.instance_config)
            vps_data.append((vps, data, specs))
    return render_template("vps.html", vps_data=vps_data)


@app.route("/vps/<string:name>")
def view_vps(name: str):
    with Session(engine) as db:
        vps = db.query(VPS).filter(VPS.name == name).first()
        if not vps or not vps.dynamic_svg:
            abort(404)
        config = db.query(SiteConfig).first()
        data = calculate_remaining(vps)
        generate_svg(vps, data, config)
    svg_url = url_for("static", filename=f"images/{name}.svg")
    if config and config.image_base_url:
        svg_abs_url = f"{config.image_base_url.rstrip('/')}/{name}.svg"
    else:
        svg_abs_url = url_for("static", filename=f"images/{name}.svg", _external=True)
    return render_template(
        "view_svg.html", name=name, svg_url=svg_url, svg_abs_url=svg_abs_url, vps_id=vps.id
    )


@app.route("/vps/<string:name>.svg")
def get_vps_image(name: str):
    with Session(engine) as db:
        vps = db.query(VPS).filter(VPS.name == name).first()
        if not vps or not vps.dynamic_svg:
            abort(404)
        config = db.query(SiteConfig).first()
        data = calculate_remaining(vps)
        svg_path = generate_svg(vps, data, config)
        directory = svg_path.parent
        return send_from_directory(directory, svg_path.name, mimetype="image/svg+xml")


if __name__ == "__main__":
    refresh_images()
    app.run(host="0.0.0.0", port=8280)
