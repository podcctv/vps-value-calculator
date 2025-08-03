from flask import Flask, send_from_directory, abort, render_template
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import date

from app.db import engine, Base
from app.models import VPS
from app.utils import calculate_remaining, generate_svg

app = Flask(__name__)
Base.metadata.create_all(bind=engine)


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
