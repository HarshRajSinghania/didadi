# 文档优先视觉方案与审查

使用 Product Design audit/get-context 与 ui-ux-pro-max。后者通用搜索给出的 landing/巨型标题不适用于本工作区，按用户给出的知识库参考覆盖。

## 当前证据与问题

1. 现有 8766 页面截图 `.local/design/01-before.png`：保存/历史可操作，但宣传式大标题、深色大卡片与 SHA 先于正文；没有稳定侧栏与文档树。技术信息占主层级，用户读写文档的入口不清楚。
2. Outline 官网 https://www.getoutline.com/ 当前实拍 `.local/design/02-outline-official.png`：浅色 collection 树、文档面包屑、正文优先、辅助目录不抢主层级。仅查看官方公开截图，未登录，不能据此证明其完整操作/无障碍表现。
3. Docmost 官方像素 https://docmost.com/screenshots/editor-hd.png，来自 https://docmost.com/ 实拍 `.local/design/03-docmost-editor.png`：左页树＋中央文档＋右评论栏；轻工具栏、阅读/编辑切换，正文不是卡片堆叠。

## 采用的方案（尺寸为本项目设计值，并非竞品测量）

- 浅灰 248px 侧栏：工作区、真实单一文档树、房间列表和可操作的新建本地测试房间；不伪造模板、收藏、多文档或团队权限。
- 52px 顶栏：面包屑、阅读/编辑、历史、讨论、示例 Agent。正文最大 760px 居中，标题 34px、正文 16px/1.75；不套大卡片。
- 默认阅读，安全呈现 Markdown；编辑切换才出现工具栏与 source 编辑器。真实标题来自 Markdown，格式按钮实际改变选中文本。
- 340px 按需右栏默认关闭。讨论对应真实 Matrix 房间，Agent 面板明确为 deterministic echo，无 LLM。任务/事务详情折叠，版本 SHA 仅在历史详情显示。
- loading 使用相同布局 skeleton；失败在编辑区就近呈现、保留草稿；冲突显示清晰横条并提供加载最新版本，不把任务日志当正文。
- 小屏折叠侧栏/右抽屉，正文保持可读；键盘焦点、label、状态反馈与 reduced-motion 必须保留。截图不能单独证明 WCAG 合规。

## 验收截图

实现后记录正常、loading、失败、conflict 四种真实渲染状态和前后对照；测试状态注入仅用于隔离 QA，不伪装为真实后端成功。正常操作必须复用真实 Synapse/Git/外部 runtime；最终提交 CI 另核验。

## 实际 QA 结果

1. 正常阅读（健康）：`.local/design/04-normal.png`，真实 Git 读回，正文居中、独立标题/段落/列表层级，右栏默认关闭。与两张官方截图同批打开对照；采用信息结构与密度，不复刻品牌/示例内容。
2. 加载（健康）：`.local/design/05-loading.png`，隔离 adapter 延迟真实文档读取，页面标注 visual regression capture；保留导航与正文版式 skeleton。
3. 失败（已修正后健康）：`.local/design/06-failure.png`，隔离 adapter 故障。初次截图显示错误后 skeleton 仍播放，已修为静态 unavailable 内容与就近 Retry；正常服务不受影响。
4. 冲突（健康）：`.local/design/07-conflict.png`，真实历史快照写入被 worker 拒绝，旧版草稿仍在编辑区，最新 Git commit 未被覆盖。只有显式“Load latest to merge”才替换草稿。
5. 正常写入与消息（健康）：浏览器保存新增正文段落，收到真实 Git/Matrix 回执；创建并进入“产品协作”私有测试房间。已有消息经 SDK 发出，外部 worker 回显可在真实 timeline 查见。版本/任务技术细节折叠。

限制：官方参考是公开截图而非登录后的全流程审计；未测试其交互或 WCAG 合规。当前仅完整观察桌面截图；响应式规则不等于全设备视觉认证。浏览器扩展侧边浮条属于用户 Chrome，不是产品 UI。最终检查以最终 PR/CI 证据为准。
