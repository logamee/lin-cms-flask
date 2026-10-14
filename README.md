<!-- # Lin-CMS-Flask -->

<h1 align="center">
  <a href="https://doc.cms.talelin.com/">
  <img src="https://doc.cms.talelin.com/left-logo.png" width="250"/></a>
  <br>
  Lin-CMS-Flask
</h1>

<h4 align="center">一个简单易用的CMS后端项目 | <a href="https://doc.cms.talelin.com/" target="_blank">Lin-CMS-Flask</a></h4>

<p align="center">
  <a href="https://github.com/logamee/lin-cms-flask/actions/workflows/ci.yml">
  <img src="https://img.shields.io/github/actions/workflow/status/logamee/lin-cms-flask/ci.yml?branch=master&label=CI" alt="CI status"></a>
  <a href="https://flask.palletsprojects.com/en/3.1.x/" rel="nofollow">
  <img src="https://img.shields.io/badge/Flask-3.1.3-green.svg" alt="Flask version" data-canonical-src="https://img.shields.io/badge/Flask-3.1.3-green.svg" style="max-width:100%;"></a>
    <a href="https://www.python.org/" rel="nofollow">
    <img src="https://img.shields.io/badge/python->=3.11,<3.15-red.svg" alt="Python version" data-canonical-src="https://img.shields.io/badge/python->=3.11,<3.15-red.svg" style="max-width:100%;">
    </a>
      <a href="https://doc.cms.talelin.com/" rel="nofollow"><img src="https://img.shields.io/badge/license-MIT-skyblue.svg" alt="License" data-canonical-src="https://img.shields.io/badge/license-MIT-skyblue.svg" style="max-width:100%;"></a>
</p>

<blockquote align="center">
  <em>Lin-CMS</em> 是林间有风团队经过大量项目实践所提炼出的一套<strong>内容管理系统框架</strong>。<br>
 本仓库在其 Flask 实现的基础上继续维护：收紧了安全默认值，补上了 CI 与部署配置，适合直接拿来二次开发。
</blockquote>

<p align="center">
  <a href="#简介">简介</a>&nbsp;|&nbsp;<a href="https://doc.cms.talelin.com/start/flask/">快速起步</a>&nbsp;
</p>

## 简介

### 什么是 Lin CMS？

Lin-CMS 是林间有风团队经过大量项目实践所提炼出的一套**内容管理系统框架**。Lin-CMS 可以有效的帮助开发者提高 CMS 的开发效率。

本项目是 Lin CMS 后端的 Flask 实现，需要前端？请访问[前端仓库](https://github.com/TaleLin/lin-cms-vue)。

### 线上 demo

[http://face.cms.talelin.com/](http://face.cms.talelin.com/)

### QQ 交流群

QQ 群号：643205479

<img class="QR-img" width="258" height="300" src="http://i1.sleeve.talelin.com/qq-group.jpeg">

### 微信公众号

微信搜索：林间有风

<img class="QR-img" src="http://i1.sleeve.talelin.com/wechat-account.jpeg">

### Lin CMS 的特点

Lin CMS 的构筑思想是有其自身特点的。

#### Lin CMS 是一个前后端分离的 CMS 解决方案

这意味着，Lin CMS 既提供后台的支撑，也有一套对应的前端系统，当然双端分离的好处不仅仅在于此。如果您心仪 Lin，却又因为技术栈的原因无法即可使用，没关系，我们也提供了更多的语言版本和框架的后端实现。为什么 Lin 要选择前后端分离的单页面架构呢？

首先，传统的网站开发更多的是采用服务端渲染的方式，需用使用一种模板语言在服务端完成页面渲染：比如 JinJa2、Jade 等。
服务端渲染的好处在于可以比较好的支持 SEO，但作为内部使用的 CMS 管理系统，SEO 并不重要。

但一个不可忽视的事实是，服务器渲染的页面到底是由前端开发者来完成，还是由服务器开发者来完成？其实都不太合适。现在已经没有多少前端开发者是了解这些服务端模板语言的，而服务器开发者本身是不太擅长开发页面的。那还是分开吧，前端用最熟悉的 Vue 写 JS 和 CSS，而服务器只关注自己的 API 即可。

其次，单页面应用程序的体验本身就要好于传统网站。

#### 框架本身已内置了 CMS 常用的功能

Lin 已经内置了 CMS 中最为常见的需求：用户管理、权限管理、日志系统等。开发者只需要集中精力开发自己的 CMS 业务即可

#### Lin CMS 本身也是一套开发规范

Lin CMS 除了内置常见的功能外，还提供了一套开发规范与工具类。换句话说，开发者无需再纠结如何验证参数？如何操作数据库？如何做全局的异常处理？API 的结构如何？前端结构应该如何组织？这些问题 Lin CMS 已经给出了解决方案。当然，如果您不喜欢 Lin 给出的架构，那么自己去实现自己的 CMS 架构也是可以的。但通常情况下，您确实无需再做出架构上的改动，Lin 可以满足绝大多数中小型的 CMS 需求。

举例来说，每个 API 都需要校验客户端传递的参数。但校验的方法有很多种，不同的开发者会有不同的构筑方案。但 Lin 提供了一套验证机制，开发者无需再纠结如何校验参数，只需模仿 Lin 的校验方案去写自己的业务即可。

还是基于这样的一个原则：Lin CMS 只需要开发者关注自己的业务开发，它已经内置了很多机制帮助开发者快速开发自己的业务。

#### 基于插件的扩展

任何优秀的框架都需要考虑到扩展。而 Lin 的扩展支持是通过插件的思想来设计的。当您需要新增一个功能时，您既可以直接在 Lin 的目录下编写代码，也可以将功能以插件的形式封装。比如，您开发了一个文章管理功能，您可以选择以插件的形式来发布，这样其他开发者通过安装您的插件就可以使用这个功能了。毫无疑问，以插件的形式封装功能将最大化代码的可复用性。您甚至可以把自己开发的插件发布，以提供给其他开发者使用。这种机制相当的棒。

#### 前端组件库支持

Lin CMS 还将提供一套类似于 Vue Element 的前端组件库，以方便前端开发者快速开发。相比于 Vue Element 或 iView 等成熟的组件库，Lin 所提供的组件库将针对 Lin CMS 的整体设计风格、交互体验等作出大量的优化，使用 Lin CMS 的组件库将更容易开发出体验更好的 CMS 系统。当然，Lin CMS 本身不限制开发者选用任何的组件库，您完全可以根据自己的喜好/习惯/熟悉度，去选择任意的一个基于 Vue 的组件库，比如前面提到的 Vue Element 和 iView 等。您甚至可以混搭使用。当然，前提是这些组件库是基于 Vue 的。

#### 完善的文档

我们将提供尽可能完善的[文档](https://doc.cms.talelin.com)
来帮助开发者使用 Lin CMS

## 开发与部署

### 环境要求

- Python >= 3.11（3.10 已停止维护，且当前依赖链不再支持）
- [uv](https://docs.astral.sh/uv/) 作为包管理器（替代旧版的 poetry，所有命令通过 `uv run` 执行）

```bash
cp .env.example .development.env   # 首次克隆必做：复制模板并填入 SECRET_KEY（缺失会拒绝启动）
uv sync                      # 安装项目 + 开发工具链（PEP 735 dev 依赖组默认包含）
uv run flask db init         # 建表 + 种子数据（与旧版命令一致；默认账号 root/123456，请尽快修改）
uv run flask run             # 启动开发服务器（默认 sqlite，读取 .development.env）
```

### 数据库

默认使用 SQLite，无需额外安装。切换数据库前需先安装对应的驱动扩展，再修改 `.development.env` / `.production.env` 中的 `SQLALCHEMY_DATABASE_URI`：

```bash
uv sync --extra mysql        # MySQL 驱动 (PyMySQL)
uv sync --extra postgres     # PostgreSQL 驱动 (psycopg 3)
```

```ini
# MySQL
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:***@localhost:3306/lincmsdev'
# PostgreSQL 注意：SQLAlchemy 2.1 起 postgresql:// 默认驱动已从 psycopg2 换为 psycopg 3，
# 请勿单独安装 psycopg2-binary，它无法匹配裸 postgresql:// 连接串
SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:***@localhost:5432/lincmsdev'
```

数据库结构由 **Flask-Migrate (Alembic)** 管理。命令习惯与旧版保持一致：

```bash
uv run flask db init         # 建表 + 种子数据（root/123456、Guest 分组、权限同步）；幂等，重复执行无副作用
uv run flask db init --force # 清空重建（确认后执行）
uv run flask db fake         # 补充示例图书数据（演示用途，手动执行）
```

> `flask db init` 内部即 `flask db upgrade`（alembic 按 alembic_version 记录幂等）；
> alembic 原生的 init（创建迁移仓库）已被有意遮蔽：`migrations/` 随仓库提交，本项目无需再 scaffold。

日常开发改了模型后：

```bash
uv run flask db migrate -m "add xxx column"   # 生成增量迁移（SQLite 自动 batch 模式）
uv run flask db upgrade                        # 应用
```

> **存量库升级到迁移体系**（一次性）：`uv run flask db stamp head`，只登记版本不执行 DDL。
> **启用插件后**（poem/oss/cos 等）：插件表只在启用时注册，必须重新 `flask db migrate` 生成增量，否则漂移。

### 测试与代码质量

```bash
uv run pytest                # 全量测试（内存 SQLite，与开发库完全隔离，可任意顺序执行）
uv run coverage run -m pytest && uv run coverage report
uv run pre-commit install    # 提交钩子：isort / black / flake8 / mypy
```

### 新增接口的装饰器顺序（重要）

`@permission_meta` 依赖函数身份匹配元信息，**必须紧贴路由装饰器、叠在一切会包装函数的装饰器（如 `@limiter.limit`）之上**：

```python
@cms_api.route("/xxx", methods=["POST"])
@permission_meta(name="某操作", module="某模块", mount=False)   # ← 紧贴 route
@limiter.limit("60 per minute")                               # ← 包装型装饰器放下面
@api.validate(...)
def your_view(json: SomeSchema):
    ...
```

顺序叠反不会报错，但该权限声明不会同步进权限表（存量行还会被当作过期数据清理），由 `tests/test_permission_sync.py` 在 CI 兜底。

### 生产部署

`requirements.txt` 由 uv.lock 导出，**请勿手工编辑**；升级依赖后重新生成：

```bash
uv lock --upgrade && uv sync && uv run pytest          # 升级 → 安装 → 回归
uv export --no-hashes --no-dev -o requirements.txt     # Docker 用（默认 sqlite，不含开发工具链）
uv export --no-hashes --no-dev --extra mysql -o requirements.txt     # Docker 用 MySQL 时
uv export --no-hashes --no-dev --extra postgres -o requirements.txt  # Docker 用 PostgreSQL 时
```

### Docker Compose 部署

```bash
# 生产模式强制要求 SECRET_KEY；写在同目录 .env 或环境变量中
echo "SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')" > .env
docker compose up -d --build
curl http://127.0.0.1:5000/health      # 存活探针（无认证）
```

容器以非 root 用户运行，启动时自动迁移（空库自动播种 root/123456），默认 SQLite 数据落在具名卷 `instance-data`；换外部数据库改 compose 中的 `SQLALCHEMY_DATABASE_URI` 即可。

推送 `v*` 标签会触发 [Release 流水线](.github/workflows/release.yml)：复用 CI 全部质量门禁，通过后自动构建镜像推送到 ghcr.io 并创建 GitHub Release。

应用通过 gunicorn + gevent 启动（见 `gunicorn.conf.py`）。**生产环境自动关闭 `/apidoc/*` 文档、`/` 与 `/hello` 演示路由；`/health` 探针始终可用。**

#### 生产环境配置清单（.{env}.env / 环境变量）

| 配置 | 必填 | 说明 |
|---|---|---|
| `SECRET_KEY` | ✅ | JWT 签名密钥，未设置启动即报错；生成：`python -c 'import secrets; print(secrets.token_hex(32))'` |
| `SQLALCHEMY_DATABASE_URI` | ✅ | 生产必须显式配置；使用 SQLite 会输出告警 |
| `FLASK_ENV` | ✅ | `development` / `production` / `test`，非法值启动即报错 |
| `CORS_ORIGINS` | 生产建议 | 开发环境**默认放行** `localhost/127.0.0.1:5173`，零配置可用；逗号分隔可覆盖（如前端跑 3000 端口时）。生产默认空（仅同源），跨域部署必配 |
| `SITE_DOMAIN` | 建议 | 文件上传外链域名；未配置时按请求 Host 拼接 |
| `RATELIMIT_STORAGE_URI` | 建议 | 限流共享存储（如 `redis://localhost:6379/0`）；缺省内存存储在多 worker 下按进程各自计数（启动有告警） |
| `PROXY_FIX` | 按需 | 反向代理后设 `True`，按 `X-Forwarded-For` 还原真实客户端 IP（限流依赖） |

> 环境变量文件模板见 `.env.example`；`.*.env` 已入 `.gitignore`，禁止提交真实密钥。

#### 安全基线（内置，无需配置）

- 密码策略：6-22 位（保持老用户习惯，无复杂度强制）
- 认证接口限流：登录/刷新/登出/验证码 60 次/分钟，注册 30 次/小时
- refresh token 有效期 7 天；`POST /cms/user/logout` 可吊销令牌，**修改/重置密码会吊销该用户全部存量令牌**
- 请求日志自动脱敏（password/token 等字段）

> 从旧版本直接升级到当前版本（跳过中间过程）的存量库：先补列
> `ALTER TABLE lin_user ADD COLUMN token_version INTEGER NOT NULL DEFAULT 0;`，
> 再执行 `uv run flask db stamp head` 登记迁移版本，之后统一走 `flask db upgrade`。

#### 从旧版本升级：一次性动作与行为变化

**一次性动作（按序执行）：**

1. 准备环境文件：`cp .env.example .development.env`（生产为 `.production.env`）并填入 `SECRET_KEY`（**缺失会拒绝启动**，旧版有公网缺省值凑合，现已移除）
2. 存量库登记迁移版本：`uv run flask db stamp head`（从未含「会话撤销」的版本直升的，先执行上面框中的 `ALTER TABLE` 补列）
3. 生产环境前后端**不同域名**部署的，必须配置 `CORS_ORIGINS` 白名单：旧版全放行，不配置会拦截跨域请求

**升级后的可感知变化（均为有意行为）：**

| 变化 | 影响 |
|---|---|
| 改密/管理员重置密码 → 该用户全部已登录设备立即下线 | 更安全；前端可调 `POST /cms/user/logout` 主动登出 |
| 认证接口限流（登录/刷新/登出/验证码 60 次/分钟，注册 30 次/小时） | 手动使用无感；自动化脚本/高频轮询会收到 429 |
| 日志查询的用户名/时间过滤真实生效 | 旧版忽略这些参数恒返回全量；现在结果可能变少（修复） |
| `/apidoc/*` 与 `/`、`/hello` 仅非生产环境可用 | 生产看文档请到预发/开发环境 |
| 启动不再自动建表；改模型需 `flask db migrate && flask db upgrade` | 开发多一步；CI 的 `flask db check` 会拦截漏迁移 |

>`flask db init`（含 `--force`）与 `flask db fake` 的命令习惯与旧版完全一致，无需改变。

## 参与贡献

- 版本历史：[CHANGELOG.md](CHANGELOG.md)
- 贡献流程与本地门禁：[CONTRIBUTING.md](CONTRIBUTING.md)
- 安全漏洞报告：[SECURITY.md](SECURITY.md)（请勿开公开 issue）
