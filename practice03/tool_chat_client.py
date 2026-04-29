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
