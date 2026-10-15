# 实施与审查证据

状态：已验证（单节点开发里程碑），已提交 draft PR #5，未部署公网、未合并。

对照计划：持久事务和事件去重、租约、固定身份凭据、原线程回复、独立 outbound worker 与 loopback 预览均已实现。新增任务/result ledger 在独立 gateway volume；Git 文档内容不迁移。运行检查和限制以 docs/VALIDATION.md 为权威。

自查重点：ACK 在 SQLite commit 后；无 AS/HS token 下发给 worker；入站与发送均 fail-closed 检查 encryption/membership；过期 lease 无法覆盖新领取；首个 result 固定用于发送恢复；Matrix 使用稳定事务 ID。预览 HTML 转义消息，CSRF token 和 loopback Host 校验，凭据不进入浏览器。无消息 eval、无公网 bind、无远端强推。

剩余范围：生产 tenant/inviter allowlist、凭据轮换、配额、任务取消和 lease 续期、真实 E2EE 用户提示、任意停机 exactly-once、Issue #3 Git hardening。示例 worker 只回显，不执行真正智能任务。
