import os
from dotenv import load_dotenv
from openai import OpenAI

def main():
    # 加载环境变量
    load_dotenv()
    print("✅ AI Agent Project Initialized!")
    print(f"📂 当前工作目录: {os.getcwd()}")

    try:
        # 连接本地LM Studio服务
        client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
            timeout=180  # 延长3分钟超时，本地GPU推理足够用
        )

        print("\n💬 正在连接本地Qwen3.5 4B模型...\n")
        
        # 关闭流式输出！先跑非流式验证连通性，本地小GPU流式极易超时断开
        response = client.chat.completions.create(
            model="qwen3.5-4b",
            messages=[
                {"role": "system", "content": "你是通义千问Qwen3.5 4B本地大模型，回答简洁自然，逻辑清晰"},
                {"role": "user", "content": "你好，简单介绍一下你自己"}
            ],
            temperature=0.7,
            stream=False  # 先关闭流式，100%不超时
        )

        print("🎉 模型回复：")
        print("-" * 60)
        print(response.choices[0].message.content)
        print("-" * 60)

    except Exception as e:
        print(f"\n❌ 运行出错：{str(e)}")

if __name__ == "__main__":
    main()