# VPS-value-calculation

[![Docker Image CI](https://github.com/podcctv/VPS-value-calculation/actions/workflows/docker-image.yml/badge.svg)](https://github.com/podcctv/VPS-value-calculation/actions/workflows/docker-image.yml)

Another VPS value calculation



## User Registration

The application now includes a simple user system. The first user to register
is automatically granted administrator privileges and can manage subsequent
accounts. After a fresh deployment, the default invitation code for
registration is `Flanker`. The user management interface allows you to
configure invitation codes and other settings.


# 💰 VPS 剩余价值计算器

一个专为 **VPS 交易** 场景设计的可视化剩余价值计算工具。通过自动计算、图片展示与链接分享，帮助你高效管理、展示、交易 VPS 资源。

---

## ✨ 项目亮点

### 🔄 动态自动更新

* **每日自动刷新**：系统每天凌晨自动重新计算剩余价值，无需手动干预
* **图片 URL 永久有效**：分享链接固定，图片内容每日同步更新
* **实时数据同步**：交易日期、剩余天数、剩余价值等信息自动实时更新
* **更新周期可调**：默认 7 天自动更新，可自定义 1\~30 天有效期

### 🎯 专为 VPS 交易设计

* **精确计算**：综合考虑购买时间、续费周期、当前汇率等因素
* **精美图片展示**：SVG 格式，适配移动端，分享更专业
* **一键复制分享**：生成图片链接，论坛、群组、网站可直接展示
* **多维数据展示**：自动生成完整 VPS 交易信息

---

## 🖼️ 图片展示内容（自动生成）

| 项目      | 内容          |
| ------- | ----------- |
| 📅 交易日期 | 自动更新时间      |
| 💰 外币汇率 | 实时汇率换算      |
| 🔁 续费价格 | 明确标注续费方案    |
| ⏰ 剩余天数  | 精确到天        |
| 💎 剩余价值 | 实时动态计算      |
| 🧾 总价值  | 包含初始投入和续费信息 |
| ⚡ 有效期   | 图片展示周期      |

---

## 🧱 Docker 化部署

本项目已支持 **一键部署**，整合所有必要服务：

* HTTP 服务：用于展示和访问 SVG 图片等数据
* 图片服务：自动生成和缓存 SVG 资源
* 数据库服务：持久化存储所有 VPS 信息与配置
* 定时任务服务：每日 0 点自动刷新剩余价值

### 📦 快速启动

```bash
git clone https://github.com/podcctv/vps-value-calculator.git
cd vps-value-calculator
docker compose up -d
```

默认数据和图片会存储在 `/opt/vps-value-calculator/data/` 与 `/opt/vps-value-calculator/static/images/` 下。

访问示例：

```
http://your-server-ip:8280/vps/xxxx.svg
```

### 🚀 使用部署脚本

仓库提供 `deploy.sh` 脚本实现一键部署或更新。脚本会自动切换到自身所在目录，可在任意位置通过绝对路径执行：

```bash
git clone https://github.com/podcctv/vps-value-calculator.git
chmod +x ./vps-value-calculator/deploy.sh
./vps-value-calculator/deploy.sh
```

脚本会自动设置持久化目录、拉取最新代码并通过 `docker compose` 重建并启动服务。

---

## 🖥️ 命令行管理

项目提供 `cli.py` 以便在终端快速管理 VPS 数据。

### 列出当前 VPS

```bash
python cli.py list
```

### 新增 VPS 条目

```bash
python cli.py add
```

直接运行 `python cli.py` 将进入交互式菜单模式。

---

## 💾 持久化与图片本地化

* 所有 VPS 数据与图片均 **本地化存储**，安全可靠
* SQLite 数据库默认保存在 `data/` 目录
* 自动生成的 SVG 图片保存在 `static/images/` 目录，可直接通过 URL 访问
* 通过数据库管理 VPS 条目，可支持 Excel 导入导出、搜索筛选等功能扩展

---

## 📈 未来规划

* [ ] 支持用户登录、管理私有 VPS 条目
* [ ] 支持 Telegram / Discord 自动推送图片
* [ ] 丰富主题样式与自定义模板
* [ ] Web 前端管理后台（支持 CRUD、数据可视化）

---

## 🛠 技术栈

* **后端**：Node.js / Python / Flask
* **前端**：React (可选) / SVG 动态模板引擎
* **数据库**：SQLite / MySQL
* **部署**：Docker + Docker Compose + Cron

---

## 🤝 项目贡献

欢迎提交 PR、Issue 或建议！若你在实际使用中遇到问题，欢迎反馈。

---

## 📄 License

MIT License


