from flask import (
    Flask,
    send_from_directory,
    abort,
    render_template,
    request,
    redirect,
    url_for,
    session,
    Response,
    jsonify,
)
import base64
import time
from urllib.parse import quote
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import date, datetime
from markupsafe import Markup

from flask_compress import Compress

from app.db import engine, Base
from app.models import VPS, User, InviteCode, SiteConfig, VisitStats
from app.utils import (
    calculate_remaining,
    generate_svg,
    parse_instance_config,
    mask_ip,
    ping_ip,
    traceroute_ip,
    run_speedtest,
    ip_to_flag,
    ip_to_isp,
    twemoji_url,
)

app = Flask(__name__)
Compress(app)
app.secret_key = "change-me"

# Cache static files for one year to leverage browser caching
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 31536000


@app.after_request
def add_cache_headers(response):
    if request.path.startswith("/static/"):
        response.headers.setdefault(
            "Cache-Control", "public, max-age=31536000, immutable"
        )
    return response
TWEMOJI_BASE = "https://cdnjs.cloudflare.com/ajax/libs/twemoji/14.0.2/svg"

# Animated favicon (16x16 diamond that cycles through colors)
FAVICON_BASE64 = (
    "R0lGODlhEAAQAIEAAP9VVQAAAAAAAAAAACH/C05FVFNDQVBFMi4wAwEAAAAh+QQBFAABACwAAAAAEAAQAAAIOgADCBwoEADBgwcBKESIUKFDhgMdSoQosWLDihYjYsRY"
    "cKPHjxxBZhS5UOPHixspcoQYICPLliUJBgQAIfkEARQAAQAsAAAAABAAEACBVf9VAAAAAAAAAAAACDoAAwgcKBAAwYMHAShEiFChQ4YDHUqEKLFiw4oWI2LEWHCjx48c"
    "QWYUuVDjx4sbKXKEGCAjy5YlCQYEACH5BAEUAAEALAAAAAAQABAAgVVV/wAAAAAAAAAAAAg6AAMIHCgQAMGDBwEoRIhQoUOGAx1KhCixYsOKFiNixFhwo8ePHEFmFLlQ"
    "48eLGylyhBggI8uWJQkGBAAh+QQBFAABACwAAAAAEAAQAIH//1UAAAAAAAAAAAAIOgADCBwoEADBgwcBKESIUKFDhgMdSoQosWLDihYjYsRYcKPHjxxBZhS5UOPHixsp"
    "coQYICPLliUJBgQAOw=="
)


@app.route("/favicon.ico")
def favicon():
    icon_bytes = base64.b64decode(FAVICON_BASE64)
    return Response(icon_bytes, mimetype="image/gif")


@app.template_filter("twemoji")
def twemoji_filter(emoji: str, width: int = 16, height: int = 16, extra_class: str = "") -> str:
    """Return an HTML img tag rendering the emoji via Twemoji.

    Allows specifying explicit width/height and an extra CSS class to
    help reserve layout space and reduce CLS.
    """
    code_points = "-".join(f"{ord(c):x}" for c in emoji)
    url = f"{TWEMOJI_BASE}/{code_points}.svg"
    return Markup(
        f'<img src="{url}" alt="{emoji}" class="twemoji {extra_class}" '
        f'width="{width}" height="{height}" '
        f'style="display:inline-block;width:{width}px;height:{height}px;vertical-align:-0.1em;">'
    )


app.add_template_filter(twemoji_url, "twemoji_url")

Base.metadata.create_all(bind=engine)


def get_current_user():
    user_id = session.get("user_id")
    if user_id:
        with Session(engine) as db:
            return db.get(User, user_id)
    return None


def get_site_config():
    with Session(engine) as db:
        return db.query(SiteConfig).first()


def get_site_stats():
    with Session(engine) as db:
        active_vps = db.query(VPS).filter(VPS.status == "active").all()
        count = len(active_vps)
        total = sum(
            calculate_remaining(vps)["remaining_value"] for vps in active_vps
        )
    return {"count": count, "total_value": round(total, 2)}


def get_visit_stats():
    with Session(engine) as db:
        stats = db.get(VisitStats, 1)
        if not stats:
            return {"visitors": 0, "crawlers": 0}
        return {"visitors": stats.visitors, "crawlers": stats.crawlers}


@app.before_request
def track_visits():
    if request.endpoint == "static":
        return
    ua = request.headers.get("User-Agent", "").lower()
    bots = ("bot", "spider", "crawl", "slurp")
    is_bot = any(keyword in ua for keyword in bots)
    with Session(engine) as db:
        stats = db.get(VisitStats, 1)
        if not stats:
            stats = VisitStats(id=1, visitors=0, crawlers=0)
            db.add(stats)
        if is_bot:
            stats.crawlers += 1
        else:
            stats.visitors += 1
        db.commit()


@app.context_processor
def inject_visit_stats():
    return {"visit_stats": get_visit_stats()}


_vps_cache = {"data": None, "time": 0}


def get_vps_data():
    now = time.time()
    if _vps_cache["data"] is not None and now - _vps_cache["time"] < 60:
        return _vps_cache["data"]
    with Session(engine) as db:
        vps_list = db.query(VPS).all()
        vps_data = []
        for vps in vps_list:
            data = calculate_remaining(vps)
            specs = parse_instance_config(vps.instance_config)
            ip_info = {
                "ip_display": mask_ip(vps.ip_address) if vps.ip_address else "-",
                "ping_status": ping_ip(vps.ip_address) if vps.ip_address else "",
                "flag": ip_to_flag(vps.ip_address) if vps.ip_address else "",
                "isp": ip_to_isp(vps.ip_address) if vps.ip_address else "-",
            }
            vps_data.append((vps, data, specs, ip_info))
        status_order = {"active": 0, "forsale": 1, "sold": 2, "inactive": 3}
        vps_data.sort(
            key=lambda item: (
                status_order.get(item[0].status, 3),
                -item[1]["remaining_value"],
            )
        )
    _vps_cache["data"] = vps_data
    _vps_cache["time"] = now
    return vps_data


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
def inject_globals():
    return {
        "current_user": get_current_user(),
        "config": get_site_config(),
        "site_stats": get_site_stats(),
        "current_year": datetime.now().year,
    }


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
            db.add(
                SiteConfig(
                    site_url="",
                    username="@Flanker",
                    copyright="xxx.com",
                )
            )
        db.commit()


init_sample()


def refresh_images():
    with Session(engine) as db:
        config = db.query(SiteConfig).first()
        vps_list = db.query(VPS).all()
        for vps in vps_list:
            if not vps.dynamic_svg or vps.status in ["sold", "inactive"]:
                continue
            data = calculate_remaining(vps)
            generate_svg(vps, data, config)


def refresh_ip_info():
    with Session(engine) as db:
        vps_list = db.query(VPS).filter(VPS.ip_address != None).all()
        for vps in vps_list:
            ip = vps.ip_address
            if ip:
                ping_ip(ip)
                ip_to_flag(ip)
                ip_to_isp(ip)


scheduler = BackgroundScheduler(timezone="Asia/Shanghai")
scheduler.add_job(refresh_images, "cron", hour=0, minute=0)
scheduler.add_job(refresh_ip_info, "interval", minutes=10)
scheduler.start()


@app.route("/robots.txt")
def robots_txt():
    lines = [
        "User-agent: *",
        "Disallow: /register",
        "Disallow: /login",
        "Allow: /vps",
    ]
    return Response("\n".join(lines), mimetype="text/plain")


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
                created_at=datetime.utcnow().replace(minute=0, second=0, microsecond=0),
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
                base_url = request.form.get("site_url", "")
                username = request.form.get("username", "")
                copyright = request.form.get("copyright", "")
                cfg = db.query(SiteConfig).first()
                if cfg:
                    cfg.site_url = base_url
                    cfg.username = username
                    cfg.copyright = copyright
                else:
                    db.add(
                        SiteConfig(
                            site_url=base_url,
                            username=username,
                            copyright=copyright,
                        )
                    )
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
                sale_percent=float(form.get("sale_percent") or 0.0),
                sale_fixed=float(form.get("sale_fixed") or 0.0),
                sale_method=form.get("sale_method"),
                push_fee=float(form.get("push_fee") or 0.0),
                push_fee_currency=form.get("push_fee_currency"),
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
        config = get_site_config()
        for vps in vps_list:
            vps.ip_display = mask_ip(vps.ip_address) if vps.ip_address else "-"
            if config and config.site_url:
                vps.abs_url = f"{config.site_url.rstrip('/')}/{quote(vps.name)}.svg"
            else:
                vps.abs_url = url_for("get_vps_image", name=vps.name, _external=True)
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
            vps.sale_percent = float(form.get("sale_percent") or 0.0)
            vps.sale_fixed = float(form.get("sale_fixed") or 0.0)
            vps.sale_method = form.get("sale_method")
            vps.push_fee = float(form.get("push_fee") or 0.0)
            vps.push_fee_currency = form.get("push_fee_currency")
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
            "sale_percent": vps.sale_percent,
            "sale_fixed": vps.sale_fixed,
            "sale_method": vps.sale_method,
            "push_fee": vps.push_fee,
            "push_fee_currency": vps.push_fee_currency,
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
@app.route("/probe")
def index():
    """Initial probe page that runs network diagnostics before showing the VPS list."""
    return render_template("probe.html")


@app.route("/vps")
def vps_list():
    vps_data = get_vps_data()
    return render_template("vps.html", vps_data=vps_data)


@app.route("/ping/<path:ip>")
def ping_status(ip: str):
    return ping_ip(ip)


@app.route("/traceroute/<path:ip>")
def traceroute_status(ip: str):
    """Return traceroute output for ``ip``."""
    return traceroute_ip(ip)


@app.route("/speedtest")
def speedtest_view():
    """Run a network speed test and return simplified results."""
    return jsonify(run_speedtest())


@app.route("/ipinfo/<path:ip>")
def ip_info(ip: str):
    """Return flag emoji and ISP name for ``ip``."""
    return jsonify({"flag": ip_to_flag(ip), "isp": ip_to_isp(ip)})


@app.route("/vps/<string:name>")
def view_vps(name: str):
    with Session(engine) as db:
        vps = db.query(VPS).filter(VPS.name == name).first()
        if not vps or not vps.dynamic_svg:
            abort(404)
        config = db.query(SiteConfig).first()
        data = calculate_remaining(vps)
        specs = parse_instance_config(vps.instance_config)
        ip_info = {
            "ip_display": mask_ip(vps.ip_address) if vps.ip_address else "-",
            "ping_status": ping_ip(vps.ip_address)
            if vps.ip_address and vps.status not in ["sold", "inactive"]
            else "",
            "flag": ip_to_flag(vps.ip_address) if vps.ip_address else "",
            "isp": ip_to_isp(vps.ip_address) if vps.ip_address else "-",
        }
        generate_svg(vps, data, config)
    svg_url = url_for("static", filename=f"images/{name}.svg")
    if config and config.site_url:
        svg_abs_url = f"{config.site_url.rstrip('/')}/{quote(name)}.svg"
    else:
        svg_abs_url = url_for("get_vps_image", name=name, _external=True)
    return render_template(
        "view_svg.html",
        name=name,
        svg_url=svg_url,
        svg_abs_url=svg_abs_url,
        vps_id=vps.id,
        vps=vps,
        data=data,
        specs=specs,
        ip_info=ip_info,
        config=config,
        today=date.today(),
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
        # Dynamic SVGs change frequently; disable caching
        return send_from_directory(
            directory,
            svg_path.name,
            mimetype="image/svg+xml",
            max_age=0,
        )


if __name__ == "__main__":
    refresh_images()
    app.run(host="0.0.0.0", port=8280)
