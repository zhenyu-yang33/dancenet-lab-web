/**
 * DanceNet.Lab 静态站点 — 后端 API 根（scheme + host + port，无尾部斜杠）
 * - 静态页与 API 同源（例如 Nginx 反代）：保持空字符串或未设置均可，请求走 `/api`.
 * - 拆分部署（HTML 在 CDN、Flask 在另一域名）：填入例如 'https://api.example.com'.
 * @type {string}
 */
window.__DANCENET_API_ORIGIN__ = '';
