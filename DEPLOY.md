# 部署指南（PaaS 方案）

本项目可部署到任意 PaaS 平台，以下以 **Railway（后端）+ Vercel（前端）** 为例。

---

## 一、部署后端（Railway）

### 1. 准备
- 注册 [Railway](https://railway.app/) 账号
- 项目推送到 GitHub

### 2. 部署步骤
1. Railway 控制台 → New Project → Deploy from GitHub repo
2. 选择你的仓库，Root Directory 填 `backend`
3. 平台会自动检测 Python 项目，执行 `pip install -r requirements.txt`
4. 启动命令：`uvicorn app.main:app --host 0.0.0.0 --port $PORT`（Procfile 已配置）

### 3. 添加 PostgreSQL 数据库
1. 在 Railway 项目中添加服务 → Database → PostgreSQL
2. 等待数据库创建完成，会自动生成 `DATABASE_URL` 环境变量

### 4. 配置环境变量
在 Variables 中添加：

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `SECRET_KEY` | JWT 密钥，**必须改**，随机生成一串 | `随机32位字符串` |
| `DEFAULT_ADMIN_USER` | 默认管理员用户名 | `admin` |
| `DEFAULT_ADMIN_PASS` | 默认管理员密码，**必须改** | `你自己的密码` |
| `DEBUG` | 调试模式 | `False` |
| `CORS_ORIGINS` | 允许的前端域名，部署后填前端地址 | `https://你的前端域名` |

> `DATABASE_URL` 在添加 PostgreSQL 服务后会自动注入，不用手动填。

### 5. 部署完成
- 访问 `https://你的服务地址/health` 应返回 `{"status":"healthy"}`
- 访问 `https://你的服务地址/docs` 可看 API 文档

---

## 二、部署前端（Vercel）

### 1. 准备
- 注册 [Vercel](https://vercel.com/) 账号
- 项目推送到 GitHub

### 2. 部署步骤
1. Vercel 控制台 → Add New → Project → Import Git 仓库
2. Framework Preset 选 **Vite**
3. Root Directory 填 `frontend`

### 3. 配置环境变量
在 Environment Variables 中添加：

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `VITE_API_BASE_URL` | 后端 API 地址 | `https://你的后端地址/api` |

> 注意：必须以 `/api` 结尾，例如 `https://schedule-api.up.railway.app/api`

### 4. 部署完成
- 部署成功后拿到一个 `*.vercel.app` 的域名
- 打开即可使用，用你设置的管理员账号登录

---

## 三、其他可选平台

### 后端替代平台
- **Zeabur**（国内访问快，中文界面）：类似 Railway，支持直接连 GitHub
- **Render**：免费额度较小，部署较慢
- **Fly.io**：需要绑信用卡

### 前端替代平台
- **Cloudflare Pages**：国内访问比 Vercel 快，免费
- **Netlify**：类似 Vercel

---

## 四、常见问题

### 1. 部署后登录报 CORS 错误
后端 `CORS_ORIGINS` 环境变量没配置对，改成你的前端域名即可。

### 2. 数据库表没有创建
SQLAlchemy 会在第一次启动时自动 `create_all`，确认 `DATABASE_URL` 正确即可。

### 3. 排课任务失败 / 超时
- Railway 免费层请求超时 30s，但排课是后台任务（BackgroundTasks），不受请求超时限制
- 注意：平台可能会在请求结束后杀掉进程，如果是这样需要换成真·后台队列
- 试用阶段建议把排课时间限制设短一点（30-60秒）

### 4. 数据怎么迁移
- 本地数据是 SQLite 的 `schedule.db`，PaaS 用的是 PostgreSQL
- 如果需要迁移数据，建议在新环境重新手动录入或导入 Excel
