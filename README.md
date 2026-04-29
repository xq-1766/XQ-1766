# AI Agent 提示词工程学习项目

本项目是一个用于学习如何与大语言模型（LLM）进行交互、配置提示词以及构建 AI Agent 的实践项目。

## 目录结构与代码功能说明

### 核心启动文件

#### [tool_chat_client.py](file:///d:/RenGongZhiNengTiShi/AI%20Coding/TiShi/tool_chat_client.py) (NEW!)
- **功能用途**：
  - **综合 AI Agent**：集成了文件管理、网络访问和实时日期感知能力的最终版助手。
  - **网络工具 (curl 模拟)**：新增 `get_url_content` 工具，支持通过 `requests` 获取网页源码，解决模型无法获取实时信息的问题。
  - **日期工具**：新增 `get_current_date` 工具，并在系统提示词中自动注入当前真实日期，消除模型对时间的“臆测”。
  - **多维度工具调用**：支持 5 个文件操作工具 + 1 个网络工具 + 1 个日期工具，共 7 个工具。
  - **完整链路**：支持流式输出、上下文记忆、无限循环对话及 Ctrl+C 优雅退出。
- **实现的教学目标**：
  - **实时信息集成**：学习如何通过网络请求工具扩展 AI 的知识边界。
  - **时间感知增强**：掌握在 System Prompt 中动态注入上下文信息（如日期）的技巧。
  - **复杂 Schema 注册**：练习编写多个不同类型工具的 OpenAI 标准 Schema。
  - **健壮性设计**：学习如何处理网络超时、请求失败等异常情况。

#### [main.py](file:///d:/RenGongZhiNengTiShi/AI%20Coding/TiShi/main.py)
- **功能用途**：项目基础启动脚本，验证环境连通性。

---

### 练习案例

#### [practice01/llm_request.py](file:///d:/RenGongZhiNengTiShi/AI%20Coding/TiShi/practice01/llm_request.py)
- **功能用途**：底层请求实现，性能监控（TPS 计算）。

#### [practice02/chatbot.py](file:///d:/RenGongZhiNengTiShi/AI%20Coding/TiShi/practice02/chatbot.py)
- **功能用途**：交互式聊天，流式输出，上下文历史管理。

#### [practice03/chatbot.py](file:///d:/RenGongZhiNengTiShi/AI%20Coding/TiShi/practice03/chatbot.py)
- **功能用途**：实现基于 System Prompt 的自定义 Function Calling 工具调用。
- **包含工具**：
  - `list_dir`：查看目录内文件属性（大小、权限、修改时间等）。
  - `rename_file`：文件重命名。
  - `delete_file`：删除指定文件。
  - `create_write_file`：新建并写入文件内容。
  - `read_file`：读取文本文件内容。
  - `get_url_content`：网络访问工具，模拟 curl 获取网页内容。
- **技术实现**：通过在全局 System Prompt 中注入完整的 JSON 格式工具定义，使模型能够自主判断并输出 JSON 格式的调用指令，程序解析后执行 Python 函数并返回结果。
- **教学目标**：掌握如何通过提示词工程（Prompt Engineering）让不支持原生 Function Call 的模型也能实现可靠的工具调用。

#### [practice04/tool_chat_client.py](file:///d:/RenGongZhiNengTiShi/AI%20Coding/TiShi/practice04/tool_chat_client.py)
- **功能用途**：在 practice03 的基础上增加了**聊天历史自动压缩总结**功能。
- **核心逻辑**：
  - **触发条件**：当用户对话超过 5 轮，或者聊天上下文总长度超过 3000 字符时，自动触发总结。
  - **压缩策略**：对当前历史记录的前 70% 进行 LLM 总结压缩，保留最后 30% 的原始对话内容。
- **教学目标**：学习如何处理长上下文（Long Context）问题，掌握基础的对话记忆管理与压缩技巧。

#### [practice04/tool_chat_client_v2.py](file:///d:/RenGongZhiNengTiShi/AI%20Coding/TiShi/practice04/tool_chat_client_v2.py) (NEW!)
- **功能用途**：在 practice04 基础版上进一步增强了**长期记忆管理**与**主动信息提取**功能。
- **核心逻辑**：
  - **5W 信息提取**：每隔 5 轮对话，Agent 会主动触发一次 LLM 任务，按照 5W 规则（Who, What, When, Where, Why）提取对话关键信息，并增量保存至 `D:\chat-log\log.txt`。
  - **历史日志检索工具**：新增 `search_chat_history` 工具，允许 Agent 读取 `log.txt` 中的历史记录。
  - **多维触发机制**：支持通过 `/search` 指令强制搜索、用户意图识别自动搜索，以及模型自主决定搜索。
- **教学目标**：掌握如何构建具有“长期记忆”的 Agent，学习主动任务触发机制以及外部知识库（简单日志文件）的集成与检索。

#### [practice05/tool_chat_client_v2.py](file:///d:/RenGongZhiNengTiShi/AI%20Coding/TiShi/practice05/tool_chat_client_v2.py) (NEW!)
- **功能用途**：集成 **AnythingLLM 知识库查询**功能。
- **核心逻辑**：
  - **AnythingLLM 集成**：通过 `anythingllm_query` 工具，使用 `subprocess` 调用 `curl` 访问本地 AnythingLLM API。
  - **文档仓库检索**：当用户提到“文档仓库”、“文件仓库”、“仓库”时，Agent 会自动调用该工具从本地知识库中检索相关信息。
  - **环境配置**：需要在 `.env` 中配置 `ANYTHINGLLM_API_KEY` 和 `ANYTHINGLLM_WORKSPACE_SLUG`。
- **教学目标**：学习如何通过 API 接口将第三方知识库（RAG 系统）集成到 Agent 中，扩展其垂直领域知识。

## 实时天气查询演示 (Feature Showcase)

### 演示指令
输入：`https://wttr.in/青城山，查询青城山明天最高、最低气温`

### 为什么需要网络工具与日期工具？
1. **模型局限性**：LLM 无法实时联网，其知识停留在训练数据截止日期。
2. **日期认知缺失**：LLM 不知道“今天”是哪一天，因此无法准确计算“明天”或“下周”的具体日期。
3. **解决方案**：
   - **日期注入**：在 System Prompt 中每次动态拼接 `datetime.now()`。
   - **网络工具**：提供 `get_url_content` 工具，让 AI 能访问 `wttr.in` 等实时数据源。

## 快速开始

1. **安装依赖**：
   ```bash
   pip install -r requirements.txt
   ```

2. **配置环境**：
   参考 `env.example` 创建 `.env` 文件，并填写你的模型地址和 API Key。

3. **运行代码**：
   - **启动最终版 AI Agent (推荐)**：`python tool_chat_client.py`
   - 运行主程序：`python main.py`
   - 运行性能测试：`python practice01/llm_request.py`
   - 启动基础聊天机器人：`python practice02/chatbot.py`
   - 启动文件操作助手：`python practice03/chatbot.py`
