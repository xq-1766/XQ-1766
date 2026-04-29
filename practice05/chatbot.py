import os
import sys
import json
import re
from dotenv import load_dotenv
from openai import OpenAI
from file_manager import (
    list_directory_contents,
    rename_file,
    delete_file,
    create_write_file,
    read_file_content,
    get_url_content
)

# 加载项目根目录环境变量
load_dotenv()

# 工具描述
TOOL_SYSTEM_PROMPT = """
你是一个AI助手，可以通过调用外部工具来完成用户请求。
你可以使用的工具包括：
1. 列出目录内容:
   - 工具名: list_dir
   - 描述: 列出指定目录下的文件和子目录，包括它们的基本属性和大小。
   - 参数:
     - path (string, 必填): 要列出内容的目录路径。
   - 返回格式: JSON字符串，包含 "contents" 列表，每个元素是文件/目录信息字典，或 "error" 字符串。

2. 重命名文件:
   - 工具名: rename_file
   - 描述: 重命名指定目录下的文件。
   - 参数:
     - directory_path (string, 必填): 文件所在的目录路径。
     - old_name (string, 必填): 文件的旧名称。
     - new_name (string, 必填): 文件的新名称。
   - 返回格式: JSON字符串，包含 "success" 字符串或 "error" 字符串。

3. 删除文件:
   - 工具名: delete_file
   - 描述: 删除指定目录下的文件。
   - 参数:
     - directory_path (string, 必填): 文件所在的目录路径。
     - file_name (string, 必填): 要删除的文件名称。
   - 返回格式: JSON字符串，包含 "success" 字符串或 "error" 字符串。

4. 创建并写入文件:
   - 工具名: create_write_file
   - 描述: 在指定目录下创建文件并写入内容。
   - 参数:
     - directory_path (string, 必填): 文件所在的目录路径。
     - file_name (string, 必填): 要创建的文件名称。
     - content (string, 必填): 要写入文件的内容。
   - 返回格式: JSON字符串，包含 "success" 字符串或 "error" 字符串。

5. 读取文件内容:
   - 工具名: read_file_content
   - 描述: 读取指定目录下的文件的内容。
   - 参数:
     - directory_path (string, 必填): 文件所在的目录路径。
     - file_name (string, 必填): 要读取的文件名称。
   - 返回格式: JSON字符串，包含 "content" 字符串 or "error" 字符串。

6. 网络访问 (curl 模拟):
   - 工具名: get_url_content
   - 描述: 通过 URL 获取网页内容（模拟 curl 功能）。
   - 参数:
     - url (string, 必填): 要访问的完整 URL。
   - 返回格式: JSON字符串，包含 "content" 字符串 or "error" 字符串。

当你需要调用工具时，请严格按照以下JSON格式输出：
{"tool_name": "工具名", "args": {"参数名1": "参数值1", "参数名2": "参数值2"}}
注意：
- 每次只能调用一个工具。
- 在调用工具后，请等待工具执行结果，不要在工具调用后直接生成回复。
- 如果用户需要你执行文件操作，你必须调用工具，而不是直接回复。
- 如果用户没有明确指定目录，你可以假设当前目录为 '.'。
- 如果用户没有明确指定文件内容，你可以询问用户。
- 如果用户没有明确指定文件名，你可以询问用户。
- 你的回复必须是纯JSON格式，不能包含任何其他文本。
- 如果你不需要调用工具，直接回复用户即可。
"""


def main():
    # 初始化本地LM Studio客户端
    client = OpenAI(
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL"),
        timeout=180
    )
    model_name = os.getenv("LLM_MODEL")

    print("=" * 50)
    print("🤖 本地AI终端聊天机器人（Qwen3.5-4B）")
    print("💡 直接输入内容聊天 | Ctrl+C 退出程序")
    print("=" * 50)

    # 对话上下文历史（永久保留多轮记忆）
    chat_history = [
        {"role": "system", "content": "你是本地私有化AI助手，回答简洁准确，牢记上下文多轮对话内容"},
        {"role": "system", "content": TOOL_SYSTEM_PROMPT}
    ]

    try:
        while True:
            # 终端输入用户消息
            user_msg = input("\n你：")
            # 追加用户对话到上下文
            chat_history.append({"role": "user", "content": user_msg})

            # 流式请求本地模型
            stream = client.chat.completions.create(
                model=model_name,
                messages=chat_history,
                temperature=0.7,
                stream=True
            )

            # 打字机逐字输出
            print("AI：", end="", flush=True)
            ai_reply = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    word = chunk.choices[0].delta.content
                    ai_reply += word
                    print(word, end="", flush=True)

            # 尝试解析工具调用
            tool_call_pattern = re.compile(r'\{"tool_name":\s*".*?",\s*"args":\s*\{.*?\}\}', re.DOTALL)
            tool_match = tool_call_pattern.search(ai_reply)

            if tool_match:
                try:
                    tool_call_json = tool_match.group(0)
                    tool_call = json.loads(tool_call_json)
                    tool_name = tool_call.get("tool_name")
                    tool_args = tool_call.get("args", {})

                    print(f"\n🤖 调用工具: {tool_name}，参数: {tool_args}")
                    tool_result = call_tool(tool_name, tool_args)
                    print(f"✅ 工具结果: {tool_result}")

                    # 将工具结果添加到对话历史，并再次调用LLM
                    chat_history.append({"role": "user", "content": f"工具执行结果: {tool_result}"})
                    # 再次调用LLM以获取基于工具结果的回复
                    stream = client.chat.completions.create(
                        model=model_name,
                        messages=chat_history,
                        temperature=0.7,
                        stream=True
                    )
                    ai_reply = ""
                    print("AI：", end="", flush=True)
                    for chunk in stream:
                        if chunk.choices[0].delta.content:
                            word = chunk.choices[0].delta.content
                            ai_reply += word
                            print(word, end="", flush=True)

                except json.JSONDecodeError:
                    print("\n❌ AI回复的工具调用格式不正确，尝试直接回复。")
                except Exception as e:
                    print(f"\n❌ 工具调用失败: {e}，尝试直接回复。")

            # AI回复存入上下文，实现连续记忆
            chat_history.append({"role": "assistant", "content": ai_reply})

    except KeyboardInterrupt:
        # Ctrl+C 优雅退出
        print("\n\n👋 对话已结束，程序正常退出")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 运行异常：{str(e)}")

def call_tool(tool_name, args):
    """
    根据工具名调用对应的文件管理函数。
    """
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
    else:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})

if __name__ == "__main__":
    main()