import os
import sys
from dotenv import load_dotenv
from openai import OpenAI

# 加载项目根目录环境变量
load_dotenv()

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
        {"role": "system", "content": "你是本地私有化AI助手，回答简洁准确，牢记上下文多轮对话内容"}
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

            # AI回复存入上下文，实现连续记忆
            chat_history.append({"role": "assistant", "content": ai_reply})

    except KeyboardInterrupt:
        # Ctrl+C 优雅退出
        print("\n\n👋 对话已结束，程序正常退出")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 运行异常：{str(e)}")

if __name__ == "__main__":
    main()