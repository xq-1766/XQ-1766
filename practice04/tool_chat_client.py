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
except ImportError:
    from practice03.file_manager import (
        list_directory_contents,
        rename_file,
        delete_file,
        create_write_file,
        read_file_content,
        get_url_content
    )

# 加载项目根目录环境变量
load_dotenv()

def get_current_date():
    """获取当前真实日期和时间"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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
    else:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})

def summarize_history(client, model_name, history):
    """
    对历史记录进行总结。
    保留前 70% 的总结，后 30% 保留原文。
    """
    if len(history) <= 2: # 至少要有两条记录才值得总结（除去初始system）
        return history

    # 提取除系统消息外的实际对话
    system_msg = history[0]
    dialogue = history[1:]
    
    # 分割点
    split_index = int(len(dialogue) * 0.7)
    to_summarize = dialogue[:split_index]
    to_keep = dialogue[split_index:]

    # 构建总结请求
    summary_prompt = "请简明扼要地总结以下对话内容，保留关键信息、工具调用结果和决策结果，用一小段话概括：\n\n"
    for msg in to_summarize:
        role = "用户" if msg["role"] == "user" else "助手"
        content = msg['content']
        # 如果是工具执行结果，特别标注
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
        
        # 构造新的历史记录
        new_history = [
            system_msg,
            {"role": "system", "content": f"以上是早期对话的总结：{summary_content}"}
        ] + to_keep
        
        print(f"[系统] 压缩完成（原 {len(history)} 条 -> 现 {len(new_history)} 条）")
        return new_history
    except Exception as e:
        print(f"[系统] 总结失败: {e}")
        return history

def main():
    client = OpenAI(
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL"),
        timeout=180
    )
    model_name = os.getenv("LLM_MODEL")

    print("=" * 50)
    print("🤖 综合 AI Agent 终端 (Integrated Assistant)")
    print("💡 支持文件管理、网络访问、日期感知")
    print("=" * 50)

    chat_history = [
        {"role": "system", "content": "你是综合 AI 助手，具备实时联网和文件操作能力。"}
    ]

    try:
        while True:
            user_msg = input("\n你：")
            chat_history.append({"role": "user", "content": user_msg})

            # 检查是否需要压缩聊天历史 (超过5轮用户输入或上下文长度超过3k)
            user_rounds = sum(1 for msg in chat_history if msg["role"] == "user")
            total_chars = sum(len(msg["content"]) for msg in chat_history)
            
            if user_rounds > 5 or total_chars > 3000:
                chat_history = summarize_history(client, model_name, chat_history)

            while True:  # 工具调用递归循环
                # 动态更新系统提示词（包含实时时间）
                current_prompt = TOOL_SYSTEM_PROMPT_TEMPLATE.format(current_time=get_current_date())
                
                messages = [{"role": "system", "content": current_prompt}] + chat_history

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

                # 解析工具调用
                tool_call_pattern = re.compile(r'\{"tool_name":\s*".*?",\s*"args":\s*\{.*?\}\}', re.DOTALL)
                tool_match = tool_call_pattern.search(ai_reply)

                if tool_match:
                    try:
                        tool_call = json.loads(tool_match.group(0))
                        tool_name = tool_call.get("tool_name")
                        tool_args = tool_call.get("args", {})

                        print(f"\n⚙️ 执行工具: {tool_name}")
                        result = call_tool(tool_name, tool_args)
                        
                        # 将 AI 的工具请求和工具执行结果存入历史
                        chat_history.append({"role": "assistant", "content": ai_reply})
                        chat_history.append({"role": "user", "content": f"工具执行结果: {result}"})
                        
                        # 继续循环，让 AI 根据工具结果进行下一次思考
                        continue 
                    except Exception as e:
                        error_msg = f"工具执行出错: {e}"
                        print(f"\n❌ {error_msg}")
                        chat_history.append({"role": "assistant", "content": ai_reply})
                        chat_history.append({"role": "user", "content": error_msg})
                        continue
                else:
                    # 没有工具调用，这是最终回复，存入历史并跳出递归循环
                    chat_history.append({"role": "assistant", "content": ai_reply})
                    break

    except KeyboardInterrupt:
        print("\n👋 程序退出")
        sys.exit(0)

if __name__ == "__main__":
    main()
