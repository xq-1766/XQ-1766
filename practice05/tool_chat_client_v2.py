import os
import sys
import json
import re
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
try:
    from file_manager import (
        list_directory_contents,
        rename_file,
        delete_file,
        create_write_file,
        read_file_content,
        get_url_content
    )
    from anythingllm import anythingllm_query
except ImportError:
    from practice05.file_manager import (
        list_directory_contents,
        rename_file,
        delete_file,
        create_write_file,
        read_file_content,
        get_url_content
    )
    from practice05.anythingllm import anythingllm_query

# 加载项目根目录环境变量
load_dotenv()

def get_current_date():
    """获取当前真实日期和时间"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def search_chat_history():
    """检索本地聊天历史日志 log.txt"""
    log_path = r"D:\chat-log\log.txt"
    if not os.path.exists(log_path):
        return json.dumps({"error": "No history log found."})
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return json.dumps({"content": content})
    except Exception as e:
        return json.dumps({"error": f"Failed to read history log: {e}"})

# 增强版工具描述
TOOL_SYSTEM_PROMPT_TEMPLATE = """
你是一个集成了多种工具的综合 AI Agent。你可以通过调用外部工具来完成用户请求。
当前系统时间: {current_time}

你可以使用的工具包括：
1. 列出目录内容 (list_dir):
   - 参数: path (string)
2. 重命名文件 (rename_file):
   - 参数: directory_path (string), old_name (string), new_name (string)
3. 删除文件 (delete_file):
   - 参数: directory_path (string), file_name (string)
4. 创建并写入文件 (create_write_file):
   - 参数: directory_path (string), file_name (string), content (string)
5. 读取文件内容 (read_file_content):
   - 参数: directory_path (string), file_name (string)
6. 网络访问 (get_url_content):
   - 描述: 通过 URL 获取网页内容（模拟 curl 功能）。常用于获取实时信息（如天气、新闻）。
   - 参数: url (string, 必须是完整的 URL，不要包含反引号或空格)
   - 技巧: 查询天气建议优先使用 `https://wttr.in/城市名`，它返回简洁的文本，非常适合处理。
7. 获取当前日期 (get_current_date):
   - 描述: 获取系统当前真实日期。
8. 检索历史日志 (search_chat_history):
   - 描述: 检索存放在 D:\\chat-log\\log.txt 中的关键信息历史记录。当用户询问“以前聊过什么”或使用 /search 时使用。
9. 查询文档仓库 (anythingllm_query):
   - 描述: 当用户提到“文档仓库”、“文件仓库”、“仓库”或需要从知识库检索信息时，使用此工具。
   - 参数: message (string, 用户的查询关键词或问题)

当你需要调用工具时，请严格按照以下 JSON 格式输出：
{{"tool_name": "工具名", "args": {{"参数名1": "参数值1"}}}}

注意：
- 每次只能调用一个工具。
- 你的回复必须是纯 JSON 格式，不能包含任何其他解释文字。
- 如果不需要调用工具，直接用自然语言回复。
- **重要**: 如果工具执行结果返回错误（如 404 或超时），请分析原因并尝试更换参数重试，或者如实告知用户，不要反复执行完全相同的错误调用。
"""

def call_tool(tool_name, args):
    if tool_name == "list_dir":
        return list_directory_contents(args.get("path", "."))
    elif tool_name == "rename_file":
        return rename_file(args.get("directory_path", "."), args.get("old_name"), args.get("new_name"))
    elif tool_name == "delete_file":
        return delete_file(args.get("directory_path", "."), args.get("file_name"))
    elif tool_name == "create_write_file":
        return create_write_file(args.get("directory_path", "."), args.get("file_name"), args.get("content", ""))
    elif tool_name == "read_file_content":
        return read_file_content(args.get("directory_path", "."), args.get("file_name"))
    elif tool_name == "get_url_content":
        return get_url_content(args.get("url"))
    elif tool_name == "get_current_date":
        return json.dumps({"current_date": get_current_date()})
    elif tool_name == "search_chat_history":
        return search_chat_history()
    elif tool_name == "anythingllm_query":
        return anythingllm_query(args.get("message"))
    else:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})

def summarize_history(client, model_name, history):
    """
    对历史记录进行总结。
    保留前 70% 的总结，后 30% 保留原文。
    """
    if len(history) <= 2: 
        return history

    system_msg = history[0]
    dialogue = history[1:]
    
    split_index = int(len(dialogue) * 0.7)
    to_summarize = dialogue[:split_index]
    to_keep = dialogue[split_index:]

    summary_prompt = "请简明扼要地总结以下对话内容，保留关键信息、工具调用结果和决策结果，用一小段话概括：\n\n"
    for msg in to_summarize:
        role = "用户" if msg["role"] == "user" else "助手"
        content = msg['content']
        if "工具执行结果" in content:
            summary_prompt += f"系统: {content}\n"
        else:
            summary_prompt += f"{role}: {content}\n"

    try:
        print("\n[系统] 正在压缩聊天上下文...")
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "你是一个历史记录总结助手。"},
                {"role": "user", "content": summary_prompt}
            ],
            temperature=0.3
        )
        summary_content = response.choices[0].message.content
        
        new_history = [
            system_msg,
            {"role": "system", "content": f"以上是早期对话的总结：{summary_content}"}
        ] + to_keep
        
        print(f"[系统] 压缩完成（原 {len(history)} 条 -> 现 {len(new_history)} 条）")
        return new_history
    except Exception as e:
        print(f"[系统] 总结失败: {e}")
        return history

def log_5w_info(client, model_name, history):
    """
    每五次聊天提取一次 5W 关键信息并存入 D:\chat-log\log.txt
    """
    print("\n[系统] 正在提取 5W 关键信息并更新日志...")
    
    # 获取最近 5 轮的对话内容
    # 注意：这里我们取最近的几条记录。一轮通常包含 user 和 assistant 各一条，
    # 如果有工具调用，记录会更多。这里简单取最后 10 条（大概 5 轮）。
    recent_history = history[-10:]
    
    extract_prompt = """
    请从以下对话中提取关键信息，按照 5W 规则（Who, What, When, Where, Why）进行提取。
    提取多条信息，每条信息占一行，格式如下：
    - [时间]: [谁] [做了什么] [在何处] [为什么]
    
    如果没有对应信息可以省略该项，但必须保留 [谁] 和 [做了什么]。
    
    对话内容：
    """
    for msg in recent_history:
        role = "用户" if msg["role"] == "user" else "助手"
        extract_prompt += f"{role}: {msg['content']}\n"

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "你是一个信息提取助手，擅长按照 5W 规则提取关键信息。"},
                {"role": "user", "content": extract_prompt}
            ],
            temperature=0.3
        )
        extracted_info = response.choices[0].message.content.strip()
        
        # 写入文件
        log_dir = r"D:\chat-log"
        log_file = os.path.join(log_dir, "log.txt")
        
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n--- 提取时间: {get_current_date()} ---\n")
            f.write(extracted_info + "\n")
            
        print(f"[系统] 5W 信息提取完成并已存入 {log_file}")
    except Exception as e:
        print(f"[系统] 5W 信息提取失败: {e}")

def main():
    client = OpenAI(
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL"),
        timeout=180
    )
    model_name = os.getenv("LLM_MODEL")

    print("=" * 50)
    print("🤖 综合 AI Agent 终端 v2 (Integrated Assistant)")
    print("💡 支持文件管理、网络访问、日志记忆、5W 提取")
    print("=" * 50)

    chat_history = [
        {"role": "system", "content": "你是综合 AI 助手，具备实时联网、文件操作、历史日志检索和文档仓库查询能力。当用户提到‘文档仓库’、‘文件仓库’、‘仓库’时，请调用 anythingllm_query 工具。"}
    ]
    
    user_input_count = 0

    try:
        while True:
            user_msg = input("\n你：")
            
            # 检查是否是 /search 开头
            force_search = False
            if user_msg.startswith("/search"):
                force_search = True
                user_msg = user_msg.replace("/search", "").strip()
                if not user_msg:
                    user_msg = "查找最近的聊天记录"

            chat_history.append({"role": "user", "content": user_msg})
            user_input_count += 1

            # 1. 每 5 次聊天提取一次 5W 信息
            if user_input_count % 5 == 0:
                log_5w_info(client, model_name, chat_history)

            # 2. 检查是否需要压缩聊天历史
            user_rounds = sum(1 for msg in chat_history if msg["role"] == "user")
            total_chars = sum(len(msg["content"]) for msg in chat_history)
            if user_rounds > 10 or total_chars > 3000: # 稍微放宽轮数限制，因为有 log.txt 了
                chat_history = summarize_history(client, model_name, chat_history)

            # 3. 确定是否需要强制搜索历史
            is_first_turn_of_msg = True

            while True:  # 工具调用递归循环
                current_prompt = TOOL_SYSTEM_PROMPT_TEMPLATE.format(current_time=get_current_date())
                
                # 如果是强制搜索且是该条消息的第一轮，可以尝试引导模型调用工具
                # 或者直接在 messages 中注入一个引导
                messages = [{"role": "system", "content": current_prompt}] + chat_history
                
                if force_search and is_first_turn_of_msg:
                    messages.append({"role": "system", "content": "用户明确要求搜索历史日志，请立即调用 search_chat_history 工具。"})

                stream = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=0.3,
                    stream=True
                )

                print("AI：", end="", flush=True)
                ai_reply = ""
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        word = chunk.choices[0].delta.content
                        ai_reply += word
                        print(word, end="", flush=True)

                is_first_turn_of_msg = False
                
                tool_call_pattern = re.compile(r'\{"tool_name":\s*".*?",\s*"args":\s*\{.*?\}\}', re.DOTALL)
                tool_match = tool_call_pattern.search(ai_reply)

                if tool_match:
                    try:
                        tool_call = json.loads(tool_match.group(0))
                        tool_name = tool_call.get("tool_name")
                        tool_args = tool_call.get("args", {})

                        print(f"\n⚙️ 执行工具: {tool_name}")
                        result = call_tool(tool_name, tool_args)
                        
                        chat_history.append({"role": "assistant", "content": ai_reply})
                        chat_history.append({"role": "user", "content": f"工具执行结果: {result}"})
                        continue 
                    except Exception as e:
                        error_msg = f"工具执行出错: {e}"
                        print(f"\n❌ {error_msg}")
                        chat_history.append({"role": "assistant", "content": ai_reply})
                        chat_history.append({"role": "user", "content": error_msg})
                        continue
                else:
                    chat_history.append({"role": "assistant", "content": ai_reply})
                    break

    except KeyboardInterrupt:
        print("\n👋 程序退出")
        sys.exit(0)

if __name__ == "__main__":
    main()
