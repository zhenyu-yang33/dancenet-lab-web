# DanceNet.Lab · 静态站点

本仓库仅包含 **一页式前端**（`index.html` + `api-config.js`），可与 **后端独立部署**。后端继续使用 **aiagent 仓库内的 `dance_teacher_demo`（Flask）**，二者通过 **统一的 HTTP `/api/**` 路径** 对接，不产生「分支覆盖主干」的版本纠缠。

## 配置 API 地址（固定 URL）

编辑 **`api-config.js`**，设置后端根地址（无末尾 `/`）：

```javascript
window.__DANCENET_API_ORIGIN__ = 'https://你的后端域名';
```

本地调试（静态页开一个端口，Flask `dance_teacher_demo` 在 `5000`）示例见 **`api-config.example.js`**：

```javascript
window.__DANCENET_API_ORIGIN__ = 'http://127.0.0.1:5000';
```

也可在浏览器调试时用查询参数单次覆盖：`?api=http%3A%2F%2F127.0.0.1%3A5000`。

若使用 **同源反向代理**（页面与 `/api` 同一域名），保持 `window.__DANCENET_API_ORIGIN__ = ''` 即可。

## 本地预览

在项目根目录：

```bash
python3 -m http.server 8080
```

访问 `http://127.0.0.1:8080`。请确保 `api-config.js` 已指向当前运行的 Flask 地址，并在后端 **`dance_teacher_demo`** 已开启 CORS（见该项目的 `app.py`，`/api/*` 已放行跨域）。

## 与 aiagent 的关系

| 组件 | 位置 |
|------|------|
| 静态站点 | **本仓库** (`dancenet-lab`) |
| 分析与聊天 API | **`aiagent` 仓库内的 `dance_teacher_demo`** |

上线时：静态资源托管（OSS / Vercel / Netlify / Nginx）；API 进程或容器单独部署。**不要**再把本页放回 aiagent 主分支里参与合并以防误覆盖——只在本仓库演进。
