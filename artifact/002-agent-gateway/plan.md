# Issue #2：持久外部 Agent 纵向演示

用户已授权实现、测试、提交、draft PR 与本地预览；不合并、不公网部署。

目标：在 main 6bfd4d8 的真实 Matrix 栈基础上，将结构化提及持久化为任务。外部进程使用独立凭据出站轮询，提交文本结果，由网关以受控身份回复原线程。事务与事件去重；已接受任务在重启后保留。SQLite 是本地单节点元数据库，Git 继续是文档内容唯一权威。此里程碑不实现 Issue #3 的多进程 Git 写入，不引入 LLM。

实现：新增 SQLite 网关和 HTTP 接口、外部示例 worker、持久 volume、Issue #2 集成 smoke；保留 Phase 0 echo。房间权限使用明确的 Agent 邀请/加入，入站与发送时均检查无加密。独立 agent token 只绑定固定 managed identity。领取用租约，任务可重投递，外部执行要求幂等；Matrix 发消息使用稳定事务 ID，不能宣称任意长停机严格 exactly-once。

验收：HTTP 认证、事务/事件重放、重启恢复、租约并发领取、错误身份/E2EE 拒绝、原 thread 回复。运行全量 unittest 和真实 Compose CI；本机 Docker 若可用则补 macOS/ARM 证据。输出本地预览与明确的验证边界。
