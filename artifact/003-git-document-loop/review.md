# 文档闭环实施审查

状态：已验证（本地单机开发范围），等待最终提交 CI；未合并、未公网部署。独立分支依赖 PR #5。

Issue #3 六项均有本地证据：独立进程 CAS、远端更新/推送竞争、提交后通知前 worker 崩溃恢复、路径/symlink 场景、固定 commit、不少于 32 项完整单测与真实 Matrix smoke。具体范围以 docs/VALIDATION.md 为权威。

实现审查：Markdown 不使用 checkout 副本，所有读回来自 Git blob；OS flock 与 update-ref CAS 协调写入；commit message 内嵌 outbox 意图，单 branch ref 是唯一提交点，避免跨 ref/跨数据库双写窗口；重试绑定 event ID/request hash；通知回执和 gateway status 处理 post-ACK 崩溃。非 force push，已知 remote rewind 拒绝；未发布提交保留并阻止成功通知。消息不能选择仓库/路径/remote，演示只授予 demo.md；凭据仅服务器持有；预览消息/Markdown 转义并检查 CSRF/Host。

剩余 MVP：生产认证/租户/房间与资源 grants、Agent 注册与 token 轮换、真正外部智能运行时、E2EE 明确交互、React 客户端/文档与任务视图、任务取消/续租与限流、网络 Git remote 与备份恢复、远端分叉人工 reconciliation UX。无破坏性恢复或自动合并。
