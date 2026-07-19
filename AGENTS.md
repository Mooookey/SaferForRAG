## 要求
每次执行任务前必须阅读本AGENTS.md，确保任务顺利进行
## 必要链接
- Presidio https://presidio.dataprivacystack.org/api/
- LLM Guard https://github.com/protectai/llm-guard
- Paddle NLP https://paddlenlp.readthedocs.io/zh/latest/llm/application/information_extraction/README.html
- 解释器：D:\Miniconda\Envs\SaferForRAG
- context7 MCP Server已经通过MCP Router启动，如果对任何API不清楚，请及时向context7发起请求
## 背景
我目前正在依托presidio+llm guard+paddle nlp制作一个简单的脱敏模块，无日志，无健全，无高安全性要求，采用明文传输。
请你按照下列要求完成任务，并在完成任务后可以提出一些你认为实用的建议
- 禁止采用测试驱动的编写方式
- 现阶段假设输入的格式一定是符合预期的，无需任何冗余的错误处理
- 除非我的指令有明显问题或者矛盾之处，否则应当在我的指令范围之内执行，无需书写额外的逻辑
- 变量需要有类型注释