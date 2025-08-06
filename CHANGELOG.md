# Changelog / 更新日志

## 2025-08-06
### Performance / 性能优化
- Introduced a 10‑minute cache for server status requests to reduce repeated network calls.
  - 为服务器状态请求引入 10 分钟缓存以减少重复网络调用。
- IP country lookups now run asynchronously during VPS page loads to prevent blocking the page render.
  - 在加载 VPS 页面时，IP 国家查询改为异步执行以避免阻塞页面渲染。
- Streamlined asset loading by bundling and minifying resources for better performance.
  - 通过打包和压缩资源来优化资产加载性能。

### Other / 其他
- Fixed deploy script to display the latest commit hash after deployment so operators can verify the running version.
  - 修复部署脚本，在部署后显示最新提交哈希以便运维验证运行版本。
- Added a spinner animation while the VPS list page fetches data, improving user feedback during loads.
  - 在 VPS 列表页面获取数据时添加加载动画，提升加载过程中的用户反馈。
- Favicon is now generated and served dynamically, eliminating the need for a static binary icon file.
  - Favicon 现在动态生成并提供，不再需要静态二进制图标文件。

## 2025-08-05
### Features / 新功能
- Added a markdown copy button for one-click sharing of generated posts.
  - 添加 Markdown 一键复制按钮以便分享生成的帖子。
- Calculated the final sale price using transfer premiums and refreshed the sale premium UI and inputs.
  - 根据转让溢价计算最终售价，并刷新溢价 UI 和输入。
- Supported TCP ping with an optional port and hid port numbers in VPS IP displays.
  - 支持带可选端口的 TCP ping，并在 VPS IP 显示中隐藏端口号。

### Fixes / 修复
- Corrected the Cloudflare beacon script path and aligned the sale calculator logic with the backend.
  - 修正 Cloudflare beacon 脚本路径并使销售计算逻辑与后端一致。
- Fixed remaining value calculation in the edit form, addressed premium calculator layout issues, and resolved negative sign display.
  - 修复编辑表单中的剩余价值计算，解决溢价计算器布局问题并修正负号显示。
- Wrapped the React script in a raw block to prevent Jinja parsing and encoded special characters in copied SVG URLs.
  - 将 React 脚本包裹在 raw 块中以避免 Jinja 解析，并对复制 SVG URL 中的特殊字符进行编码。

### Documentation / 文档
- Recorded recent updates in the project documentation.
  - 在项目文档中记录最近的更新。

### Styling / 样式
- Beautified the premium calculation section and aligned related input fields for a consistent appearance.
  - 美化溢价计算部分并对齐相关输入字段以保持一致外观。

## 2025-08-04
### Performance & UI / 性能与界面
- Adjusted VPS card and container widths to accommodate varying content and viewport sizes.
  - 调整 VPS 卡片及容器宽度以适应不同内容和视口尺寸。
- Enabled wheel-based scaling for VPS cards and refined layout spacing.
  - 启用鼠标滚轮缩放 VPS 卡片并优化布局间距。
- Displayed ISP information for VPS and scoped SVG styles to prevent global effects.
  - 显示 VPS 的 ISP 信息并限定 SVG 样式范围以避免全局影响。
- Various fixes to ensure cards fit the viewport and maintain consistent layout.
  - 多项修复以确保卡片适应视口并保持一致布局。

## 2025-08-03
### Infrastructure & Performance / 基础设施与性能
- Served Tailwind locally and reduced card container margins for faster loads.
  - 本地提供 Tailwind 并减少卡片容器边距以加快加载。
- Optimized VPS card layout with responsive styles and mobile support.
  - 使用响应式样式优化 VPS 卡片布局并支持移动端。
- Added IP flag lookup using ip-api and improved async handling for network status.
  - 使用 ip-api 进行 IP 国旗查询并改进网络状态的异步处理。
- Enhanced VPS forms, dashboards, and SVG display for better usability.
  - 改进 VPS 表单、仪表盘和 SVG 显示以提升可用性。

### Earlier / 更早
- Initial Dockerized release with CLI utilities, migrations, and templates.
  - 初始发布，包含 Docker 化环境、CLI 工具、迁移及模板。
