# 部署指南

本文档记录了项目从 0 到 1 部署到公网的完整流程，基于实际操作验证。

**技术栈：** FastAPI（后端） + Vue3/Vite（前端） + SQLite（默认，可切 PostgreSQL）

---

## 方案选择

| 方案 | 后端 | 前端 | 国内访问速度 | 免费额度 | 推荐度 |
|------|------|------|-------------|---------|--------|
| **方案A（国内推荐）** | Zeabur | Cloudflare Pages | ⭐⭐⭐⭐ | 充足 | ✅ 推荐 |
| 方案B（海外） | Railway | Vercel | ⭐⭐ | 充足 | 海外用户推荐 |

> **为什么选 Zeabur + Cloudflare Pages？**
> - Zeabur：国内团队开发、中文界面、有国内/香港节点、支持 Docker 部署、免费额度够用
> - Cloudflare Pages：Cloudflare 全球 CDN，国内访问比 Vercel 快很多、免费

---

## 方案 A：Zeabur + Cloudflare Pages（国内推荐）

---

## 一、准备工作

### 1. 代码推送到 GitHub
```bash
git init
git add -A
git commit -m "初始提交"
git remote add origin https://github.com/你的用户名/仓库名.git
git push -u origin main
```

### 2. 项目中已有的部署配置
- `Dockerfile` — 后端 Docker 镜像构建文件（项目根目录，Zeabur / Railway 通用）
- `frontend/public/_redirects` — Cloudflare Pages SPA 路由重写配置
- `frontend/vercel.json` — Vercel SPA 路由重写配置
- `backend/requirements.txt` — Python 依赖
- `.gitignore` — 忽略数据库、环境变量等敏感文件

---

## 二、部署后端（Zeabur）

### 1. 注册账号
- 打开 https://zeabur.com/ 注册账号（支持微信/手机号/GitHub 登录）
- 新用户有免费额度，个人使用完全够

### 2. 部署服务
1. 登录后点 **新建项目** → **部署服务**
2. 选择 **从 Git 仓库导入** → 授权 GitHub → 选择你的仓库（如 `scheduling-system`）
3. 部署配置：
   - **构建方式**：选择 **Dockerfile**
   - **Dockerfile 路径**：`Dockerfile`（项目根目录的那个）
   - **监听端口**：`8000`
4. 点 **部署**，等待构建完成

### 3. 绑定域名
1. 进入服务详情页 → **网络** → **绑定域名**
2. 可以用 Zeabur 提供的免费域名（`xxx.zeabur.app`），也可以绑自己的域名
3. 保存好这个地址，前端配置要用到

### 4. 配置环境变量
在服务详情页 → **变量** 中添加：

| 变量名 | 必填 | 说明 | 示例值 |
|--------|------|------|--------|
| `SECRET_KEY` | ✅ | JWT 签名密钥，**必须改成随机字符串** | `随便一串长字符` |
| `DEFAULT_ADMIN_PASS` | ✅ | 默认管理员密码 | `Admin@2024` |
| `DEFAULT_ADMIN_USER` | ❌ | 默认管理员用户名，默认 `admin` | `admin` |
| `DEBUG` | ❌ | 调试模式，生产环境设 `False` | `False` |
| `CORS_ORIGINS` | ❌ | 允许的前端域名（逗号分隔多个），默认 `*` | `https://你的前端域名` |
| `DATABASE_URL` | ❌ | 数据库地址，默认 SQLite | 加 PostgreSQL 后自动注入 |

> 修改环境变量后需要 **重新部署** 才会生效。

### 5. 验证部署
访问 `https://你的域名/health`，应返回：
```json
{"status":"healthy"}
```

访问 `https://你的域名/docs` 可看到 Swagger API 文档。

### 6. （可选）添加 MySQL / PostgreSQL 数据库
默认用的是 SQLite 文件数据库，容器重建数据会丢。要持久化的话：
1. Zeabur 项目页 → **添加服务** → **MySQL** 或 **PostgreSQL**
2. 等待创建完成，在后端服务的变量中配置 `DATABASE_URL`
3. 重启后端服务即可自动切换（SQLAlchemy 会自动建表）

> 注意：切换数据库后，之前的演示数据都会清空，需要重新录入或导入。

---

## 三、部署前端（Cloudflare Pages）

### 1. 注册账号
- 打开 https://pages.cloudflare.com/ 注册（支持 GitHub 登录）
- Free 计划免费，够用

### 2. 创建项目
1. 登录 Cloudflare Dashboard → **Workers & Pages** → **Create application** → **Pages** 标签
2. 点 **Connect to Git** → 授权 GitHub → 选择你的仓库
3. 点 **Begin setup**

### 3. 配置构建参数
- **Project name**：随便填，会作为子域名
- **Production branch**：`main`
- **Framework preset**：选 **Vite**
- **Build command**：`npm run build`
- **Build output directory**：`dist`
- **Root directory**：点 **Edit**，填 `frontend`

### 4. 配置环境变量
在 **Environment variables** → **Production** 中添加：

| 变量名 | 值 |
|--------|-----|
| `VITE_API_BASE_URL` | `https://你的后端域名/api` |

> ⚠️ **重要**：值必须以 `/api` 结尾，例如：`https://scheduling-system.zeabur.app/api`
>
> 修改环境变量后需要 **重新部署（Redeploy）** 才会生效。

### 5. 部署
点 **Save and Deploy**，等待 1-2 分钟构建完成。

### 6. 验证
部署成功后访问分配的 `*.pages.dev` 域名，用管理员账号登录：
- 用户名：`admin`（或你设置的 DEFAULT_ADMIN_USER）
- 密码：你设置的 `DEFAULT_ADMIN_PASS`（默认 `admin123`）

---

## 方案 B：Railway + Vercel（海外）

### B.1 部署后端（Railway）

### 1. 注册账号
- 打开 https://railway.app/ 注册账号（GitHub 登录即可）
- 新用户有 $5 免费额度，试用完全够

### 2. 部署服务
1. 点 **New Project** → **Deploy from GitHub repo**
2. 选择你的仓库（如 `scheduling-system`）
3. 点 **Deploy** 开始部署（先不用管配置，会失败，正常）
4. 构建会失败 — 因为项目是 monorepo 结构，Railway 识别不了
5. 失败后在 **Settings** 里配置：
   - Builder 改成 **Dockerfile**
   - Dockerfile Path 填 `Dockerfile`（项目根目录的那个）
6. 或者更简单：确认根目录 `railway.json` 配置正确，重新 push 一次代码，Railway 会自动读取

> **关于 Dockerfile**：项目根目录的 `Dockerfile` 会复制 `backend/` 下的代码和依赖，构建上下文是仓库根目录。

### 3. 生成公网域名
1. 进入服务详情页 → **Settings** → **Networking**
2. 点 **Generate Domain**，会自动分配一个 `xxx.up.railway.app` 的域名
3. 保存好这个地址，前端配置要用到

### 4. 配置环境变量
在 **Variables** 标签中添加：

| 变量名 | 必填 | 说明 | 示例值 |
|--------|------|------|--------|
| `SECRET_KEY` | ✅ | JWT 签名密钥，**必须改成随机字符串** | `随便一串长字符` |
| `DEFAULT_ADMIN_PASS` | ✅ | 默认管理员密码 | `Admin@2024` |
| `DEFAULT_ADMIN_USER` | ❌ | 默认管理员用户名，默认 `admin` | `admin` |
| `DEBUG` | ❌ | 调试模式，生产环境设 `False` | `False` |
| `CORS_ORIGINS` | ❌ | 允许的前端域名（逗号分隔多个），默认 `*` | `https://你的前端域名` |
| `DATABASE_URL` | ❌ | 数据库地址，默认 SQLite | 加 PostgreSQL 后自动注入 |

### 5. 验证部署
访问 `https://你的域名/health`，应返回：
```json
{"status":"healthy"}
```

访问 `https://你的域名/docs` 可看到 Swagger API 文档。

### 6. （可选）添加 PostgreSQL 数据库
默认用的是 SQLite 文件数据库，容器重建数据会丢。要持久化的话：
1. Railway 项目页 → **Add Service** → **Database** → **Add PostgreSQL**
2. 等待创建完成，`DATABASE_URL` 会自动注入到后端服务
3. 重启后端服务即可自动切换到 PostgreSQL（SQLAlchemy 会自动建表）

> 注意：切换数据库后，之前的演示数据都会清空，需要重新录入或导入。

---

### B.2 部署前端（Vercel）

#### 1. 注册账号
- 打开 https://vercel.com/ 注册（GitHub 登录即可）
- Hobby 计划免费，够用

### 2. 导入项目
1. **Add New** → **Project** → Import 你的 GitHub 仓库
2. **Configure Project** 页面：
   - **Framework Preset**：选 **Vite**
   - **Root Directory**：点 **Edit**，填 `frontend`

#### 3. 配置环境变量
在 Environment Variables 区域添加：

| 变量名 | 类型 | 值 |
|--------|------|-----|
| `VITE_API_BASE_URL` | Config | `https://你的后端域名/api` |

> ⚠️ **重要**：类型必须选 **Config**，不能选 Secret。`VITE_` 开头的变量会被打包进前端代码，Secret 类型在构建时读不到。
>
> 值必须以 `/api` 结尾，例如：`https://scheduling-system-production.up.railway.app/api`

#### 4. 部署
点 **Deploy**，等待 1-2 分钟构建完成。

#### 5. 验证
部署成功后访问分配的 `*.vercel.app` 域名，用管理员账号登录：
- 用户名：`admin`（或你设置的 DEFAULT_ADMIN_USER）
- 密码：你设置的 `DEFAULT_ADMIN_PASS`（默认 `admin123`）

---

## 四、更新部署

代码推送到 GitHub 的 main 分支后，所有平台都会自动重新部署：

| 平台 | 自动部署 |
|------|---------|
| Zeabur | ✅ 自动 |
| Cloudflare Pages | ✅ 自动 |
| Railway | ✅ 自动 |
| Vercel | ✅ 自动 |

不需要手动操作。

---

## 五、常见问题 & 踩坑记录

### ❌ 构建失败：`/requirements.txt: not found`
**原因**：Dockerfile 在 backend 目录，但构建上下文在根目录，`COPY requirements.txt` 找不到文件。
**解决**：Dockerfile 放项目根目录，用 `COPY backend/requirements.txt .` 和 `COPY backend/ .`（本项目已配置好）。

### ❌ 部署失败：Healthcheck failure / 健康检查失败
**原因**：健康检查路径或端口配置不对。
**解决**：确认监听端口是 `8000`，健康检查路径设为空或 `/health`。

### ❌ 前端环境变量不生效
**原因**：`VITE_` 变量是构建时注入的，修改环境变量后必须 **重新部署（Redeploy）** 才会生效。
**解决**：改完变量后点重新部署。

### ❌ 登录后所有接口都报 401
**原因**：`VITE_API_BASE_URL` 配置不对，或者构建时没注入。
**解决**：确认值正确（带 `/api` 后缀），然后重新部署。

### ❌ Cloudflare Pages 刷新页面 404
**原因**：SPA 路由重写没配置。
**解决**：确认 `frontend/public/_redirects` 文件存在，内容为 `/* /index.html 200`（本项目已添加）。

### ❌ 数据会丢吗
- 用 SQLite（默认）：**会丢**，容器重建/部署新版本就没了
- 用 MySQL / PostgreSQL：**不会丢**，数据存在数据库服务里

建议正式使用前加上数据库服务。

---

## 六、环境变量总表

### 后端环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `DATABASE_URL` | `sqlite:///./schedule.db` | 数据库连接串 |
| `SECRET_KEY` | `your-secret-key-change-in-production` | JWT 密钥，生产必须改 |
| `ALGORITHM` | `HS256` | JWT 算法 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440`（24小时） | Token 过期时间 |
| `DEBUG` | `False` | 调试模式 |
| `CORS_ORIGINS` | `*` | 允许的前端域名，逗号分隔 |
| `DEFAULT_ADMIN_USER` | `admin` | 首次启动创建的管理员用户名 |
| `DEFAULT_ADMIN_PASS` | `admin123` | 首次启动创建的管理员密码 |
| `DEFAULT_SCHEDULE_TIME_LIMIT` | `120` | 默认排课时间限制（秒） |
| `DEFAULT_DAYS_PER_WEEK` | `5` | 默认每周天数 |
| `DEFAULT_SECTIONS_PER_DAY` | `10` | 默认每天节数 |

### 前端环境变量

| 变量名 | 说明 |
|--------|------|
| `VITE_API_BASE_URL` | 后端 API 地址（必须以 `/api` 结尾） |
