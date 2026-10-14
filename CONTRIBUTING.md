# 贡献指南

感谢你愿意为 Lin-CMS-Flask 贡献代码。

## 开发环境

```bash
git clone git@github.com:logamee/lin-cms-flask.git
cd lin-cms-flask
uv sync                       # 安装依赖与开发工具链（按 uv.lock 精确还原）
uv run pre-commit install     # 启用提交前检查（black/isort/flake8 等）

cp .env.example .development.env
# 填入 SECRET_KEY：python -c 'import secrets; print(secrets.token_hex(32))'
uv run flask db init          # 建表 + 种子（root/123456）
```

## 提交前自查（CI 同款门禁，本地先过再推）

```bash
uv run flake8 app starter.py tests
uv run black --check app starter.py tests && uv run isort --check-only app starter.py tests
uv run mypy
uv run pytest -q
```

要求：

- 全部通过；`uv run coverage run -m pytest -q && uv run coverage report` 总覆盖率不得低于 70%，新增代码请顺手补测试
- 涉及模型变更必须同时提供 alembic 迁移（`uv run flask db migrate`），并确认 CI 的迁移检查（全新库 upgrade + `flask db check` 无漂移）通过
- 新增带权限的接口时，`@permission_meta` 必须紧贴路由装饰器、位于 `@limiter.limit` 等包装型装饰器之上——顺序叠反不会报错，但权限声明不会同步进权限表（`tests/test_permission_sync.py` 会拦）
- 不引入新的生产依赖除非必要；引入了请同步更新 `pyproject.toml` 并执行 `uv lock` 与 `uv export --no-hashes --no-dev -o requirements.txt`

## 提交规范

使用 Conventional Commits（`feat:` / `fix:` / `docs:` / `chore:` / `refactor:` / `test:`），与现有 git 历史保持一致。

## PR 流程

1. 从 master 拉出特性分支
2. 提交 PR 并填写模板中的自查清单
3. CI 全绿后由维护者 review 合入
4. 用户可见的行为变更请在 `CHANGELOG.md` 的 Unreleased 段补一条

## 报告问题

- 缺陷/功能建议请用 issue 模板（.github/ISSUE_TEMPLATE/）
- 安全漏洞请勿开公开 issue，见 [SECURITY.md](SECURITY.md)
