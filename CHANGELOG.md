# Changelog

本项目的所有重要变更都记录在此文件中。
格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [0.7.0] - 2026-10-14

以"可二次开发的后端脚手架"为目标的安全加固与工程化版本。

### 新增

- CI 流水线（flake8 / black / isort / mypy / pytest / 全新库迁移 + 模型漂移检查），覆盖率门槛 70%
- Release 流水线：推送 `v*` 标签自动构建镜像推 ghcr.io 并创建 GitHub Release
- `GET /health` 存活探针（无认证，供容器编排与反向代理使用）
- 测试套件：安全加固、会话吊销（token_version）、框架核心、OpenAPI 契约、插件加载链路等（69+ 用例）
- `app/config/test.py` 测试环境配置（内存库，关闭限流）
- `.env.example` 环境变量模板；`.development.env` / `.production.env` 移出版本库
- 文档：CONTRIBUTING.md、SECURITY.md、issue/PR 模板
- 开发工具链迁移到 PEP 735 `[dependency-groups]`，`uv sync` 一条命令还原开发环境

### 变更

- **[破坏性]** `SECRET_KEY` 必须显式提供：未设置或仍为模板占位符时启动失败（原版内置公开缺省值）
- **[破坏性]** `flask db init` 语义定制为"迁移到最新 + 空库自动播种"（Root/Guest 分组、root 用户、权限）；alembic 原生 init 被安全遮蔽，`migrations/` 已随仓库提供
- 刷新令牌有效期收紧为 7 天；改密/禁用用户令全量旧令牌失效
- 认证类接口默认限流（flask-limiter），生产环境支持 redis 共享存储
- CORS 默认收紧为仅同源；开发环境放行本地前端 dev server
- 生产环境关闭 Swagger UI 与 OpenAPI 规范导出
- Docker 镜像以非 root 用户运行；compose 提供 SECRET_KEY/数据库注入、SQLite 具名卷与容器健康检查
- 依赖全面升级（Flask 3.1 / SQLAlchemy 2.1 / Pydantic 2 / Spectree 3 / gevent 26 等）

### 修复

- 刷新令牌 JWT identity 规范化（上游 #237）
- Pydantic 2 与 Spectree 兼容层问题
- `注册`/`刷新令牌` 两条权限声明因装饰器叠层顺序失效（`@limiter.limit` 叠在 `@permission_meta` 外层改变函数身份，导致声明不入权限表、存量行被误清理）；修正后存量库下次启动自动补回

## [0.6.0]

- 核心库并入工程源码（不再依赖外部 lin-cms 包），引入 uv 工作流
- 升级 Pydantic 2 与 Spectree，补充类型注解

更早的历史版本请查阅 git log。
