# Issue #3 文档闭环

目标：在依赖 draft PR #5 的独立分支把文档读写接入真实 Matrix/外部 worker，并通过 Issue #3 六项验收。用户已授权实现、测试、提交、draft PR 与本地预览。既有 8765 服务保持运行，新文档预览用 8766；不合并、不公网部署、不配置用户凭据或模型。

设计：专用 bare Git 仓库存 Markdown，不用 checkout/index 文件作为内容副本；私有临时 index + Git plumbing + 原子 update-ref，OS flock 跨进程序列化。事件 ID 与通知意图写入 commit message，单个 branch ref 更新构成以 Git 为权威的持久 outbox；回执 ref 在通知成功后写入。worker 重试复用已有 operation commit，崩溃后不重复写文档。读取固定 commit，blob CAS 拒绝旧版本。

远端只接受显式本地目录，用 fetch + fast-forward 同步与普通非 force push；远端竞争导致冲突，保留本地未发布提交/outbox，不自动丢弃或 force push。模拟提交后、通知前崩溃，验证重新打开仓库/重启 worker 可恢复。

安全边界：专用服务拥有的 bare 仓库，非任意用户仓库；消息无法指定路径/远端，演示仅 demo.md。所有 Markdown 以转义纯文本显示；预览使用现有固定测试房间、server-side token、CSRF/Host 限制。不把该本地权限模型称为生产多租户授权。

验证：独立进程竞争同一 base、外部远端更新/推送竞争、operation 幂等、outbox 失败重试/崩溃、路径穿越与 symlink 替换、不可变固定引用；原有 Matrix CI 保持通过，新增真实 Matrix 文档 smoke、浏览器保存/读回/通知/冲突演示。测试证据写 docs/VALIDATION.md，draft PR 明示依赖 #5。
