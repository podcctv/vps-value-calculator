# VPS-value-calculation

[简体中文](./README.md) | English

Another VPS value calculation

## 📚 Documentation

- [Changelog](./CHANGELOG_EN.md)

## 💰 VPS Residual Value Calculator

A visual tool designed for **VPS trading** scenarios. It automatically calculates residual value, renders images, and provides shareable links, helping you manage, display, and trade VPS resources efficiently.

![image](https://github.com/user-attachments/assets/6e749447-0aa8-47ff-a381-7cbe044f33b1)

---

## 📰 Latest Updates

* Fixed residual value calculation on the edit page and unified the final price formula across all pages.
* Supports automatic final sale price calculation based on transfer premium with consistent logic between front end and back end.
* Improved premium input and display, including layout adjustments and negative value handling.

---

## ✨ Highlights

### 🔄 Automatic Daily Updates

* **Daily auto-refresh** at midnight without manual intervention
* **Permanent image URLs** – share links remain fixed while content updates daily
* **Real-time data sync** for trade date, remaining days, residual value, and more

### 🎯 Tailored for VPS Trading

* **Accurate calculations** considering purchase time, renewal cycle, and exchange rate
* **Beautiful SVG output** optimized for mobile sharing
* **One-click link copy** for easy sharing
* **Rich data display** covering complete VPS trading information

---

## 🖼️ Generated Image Content

| Item | Description |
| --- | --- |
| 📅 Trade Date | Automatically updated |
| 💰 Exchange Rate | Real-time currency conversion |
| 🔁 Renewal Price | Renewal plan clearly marked |
| ⏰ Remaining Days | Accurate to the day |
| 💎 Residual Value | Calculated in real time |
| 🧾 Total Value | Includes initial investment and renewals |
| ⚡ Validity | Image validity period |

---

## 🧱 Docker Deployment

This project supports **one-click deployment** with all required services:

* HTTP service for displaying SVG images and data
* Image service for generating and caching SVG resources
* Database service for persistent storage of VPS information and configurations
* Scheduled task service to refresh residual value daily at midnight

### 📦 Quick Start

```
git clone https://github.com/podcctv/vps-value-calculator.git
cd vps-value-calculator
docker compose up -d
```

Default data and images are stored at `/opt/vps-value-calculator/data/` and `/opt/vps-value-calculator/static/images/`.

Access example:

```
http://your-server-ip:8280/vps/xxxx.svg
```

### 🚀 Deployment Script

Use the `deploy.sh` script for one-click deployment or updates. It automatically switches to its own directory and can be run from anywhere:

```
git clone https://github.com/podcctv/vps-value-calculator.git
chmod +x ./vps-value-calculator/deploy.sh
./vps-value-calculator/deploy.sh
```

The script sets up persistent directories, pulls the latest code, and rebuilds the service via `docker compose`.

### 🐳 Prebuilt Image

If you only need to run the service, use the prebuilt image:

```
docker pull ghcr.io/podcctv/vps-value-calculator:latest
docker run -d --name vps-value-calculator -p 8280:8280 \
  -v /opt/vps-value-calculator/data:/app/data \
  -v /opt/vps-value-calculator/static/images:/app/static/images \
  ghcr.io/podcctv/vps-value-calculator:latest
```

Data and images will be saved to `/opt/vps-value-calculator/data/` and `/opt/vps-value-calculator/static/images/`.

---

## User Registration

The project includes a simple user system. The first registered user automatically gains admin privileges and can manage subsequent accounts. For a fresh deployment, the default invite code is `Flanker`. You can configure the invite code and other settings in the user management interface.

![image](https://github.com/user-attachments/assets/0fa666c8-6c4f-42f7-953f-ae09cc60c306)

## 🖥️ CLI Management

`cli.py` provides terminal-based management of VPS data.

### List VPS Records

```
python cli.py list
```

### Add a VPS Record

```
python cli.py add
```

Running `python cli.py` opens an interactive menu.

---

## 💾 Persistence & Local Images

* All VPS data and images are stored locally for security
* The SQLite database is stored in the `data/` directory
* Generated SVG images are saved in `static/images/` and can be accessed via URL
* Managing VPS entries via the database allows future extensions like Excel import/export and filtering

---

## 📈 Roadmap

* [ ] User login and private VPS entries
* [ ] Telegram / Discord automatic image push
* [ ] Rich themes and customizable templates
* [ ] Web-based admin panel with CRUD and data visualization

---

## 🛠 Tech Stack

* **Backend**: Node.js / Python / Flask
* **Frontend**: React (optional) / SVG template engine
* **Database**: SQLite / MySQL
* **Deployment**: Docker + Docker Compose + Cron

---

## 🤝 Contributing

PRs, issues, and suggestions are welcome! Feel free to report any problems you encounter during real-world use.

---

## 📄 License

MIT License

