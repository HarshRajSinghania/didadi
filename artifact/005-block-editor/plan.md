# 块式编辑里程碑

用户明确要求 Notion/飞书式编辑，授权实现、独立评审、修复、合入和验证。原始 Markdown 文本框不满足需求。

选型：Milkdown Crepe 7.22.3（MIT，Markdown/Remark/ProseMirror，原生块菜单、拖拽、历史）；TipTap 3.32.0（MIT，但 Markdown 扩展仍 beta，需要更多 UI 组装）；BlockNote 0.56.0（MPL-2.0，默认块 JSON，Markdown 导出不能作为无损通用存储）。不使用 Tela 代码。

实现：React 生命周期封装成熟编辑器，编辑完整 Markdown 正文；禁用图片上传、表格、LaTeX 等本里程碑外功能；保留阅读、草稿、Git 历史、冲突副本、Matrix 保存链路。仅用户编辑才序列化并更新草稿，不因打开编辑模式自动重写 Git 内容。明确不保证 Markdown 源码排版字节级不变。

验收：标题、段落、列表、任务列表、引用、代码块，斜杠菜单、块操作/拖拽，撤销重做、中文组合输入和粘贴；保存后重开和冲突保稿。单元/编辑器 round-trip、真实浏览器和现有真实 Matrix SDK CI 分开记录。合成 Vercel 预览仍只使用浏览器示例数据。
