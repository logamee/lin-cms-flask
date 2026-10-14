## 变更说明

<!-- 做了什么、为什么这么做；关联的 issue 编号（如 Closes #123） -->

## 变更类型

- [ ] feat：新功能
- [ ] fix：缺陷修复
- [ ] docs：文档
- [ ] refactor：重构
- [ ] chore：工程化/依赖

## 自查清单

- [ ] 本地已跑 CI 同款门禁：flake8 / black+isort / mypy / pytest
- [ ] 涉及模型变更时已提供 alembic 迁移（`flask db migrate`），且全新库 `flask db upgrade && flask db check` 无漂移
- [ ] 新增/变更行为已有测试覆盖
- [ ] 用户可见的行为变更已在 CHANGELOG.md 补充条目
- [ ] 不包含任何密钥/密码/内网地址
