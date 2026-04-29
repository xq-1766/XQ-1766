import os
import json
import time
import urllib.request
import urllib.error
from dotenv import load_dotenv

def test_llm_request():
    # 1. 加载项目根目录下的 .env 文件
    # 由于当前文件在 practice01 目录下，.env 在上一级
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if not os.path.exists(env_path):
        print(f"❌ 未找到 .env 文件: {env_path}")
        print("请先根据 env.example 创建 .env 文件并填写配置。")
        return

    load_dotenv(env_path)

    # 2. 获取配置信息
    base_url = os.getenv("LLM_BASE_URL", "").rstrip('/')
    model = os.getenv("LLM_MODEL", "")
    api_key = os.getenv("LLM_API_KEY", "")

    if not base_url or not model:
        print("❌ 错误: LLM_BASE_URL 或 LLM_MODEL 未在 .env 中定义")
        return

    # 构造 OpenAI 兼容的 Chat Completions URL
    url = f"{base_url}/chat/completions"
    
    # 准备请求数据
    data = {
        "model": model,
        "messages": [
            {"role": "user", "content": "请写一段话，简要介绍什么是 AI Agent。"}
        ],
        "temperature": 0.7
    }
    
    # 准备请求头
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    print(f"🚀 正在发送请求到: {url}")
    print(f"🤖 使用模型: {model}\n")

    # 3. 发送请求并统计性能
    start_time = time.time()
    
    try:
        req = urllib.request.Request(
            url, 
            data=json.dumps(data).encode('utf-8'), 
            headers=headers, 
            method='POST'
        )
        
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode('utf-8')
            end_time = time.time()
            
            # 解析响应
            result = json.loads(res_body)
            content = result['choices'][0]['message']['content']
            usage = result.get('usage', {})
            
            # 提取 token 消耗
            prompt_tokens = usage.get('prompt_tokens', 0)
            completion_tokens = usage.get('completion_tokens', 0)
            total_tokens = usage.get('total_tokens', 0)
            
            # 计算时间
            duration = end_time - start_time
            
            # 计算速度 (Tokens Per Second)
            # 通常以生成的 completion_tokens 来计算生成速度
            tps = completion_tokens / duration if duration > 0 else 0

            # 4. 打印结果
            print("📝 模型回复内容：")
            print("-" * 40)
            print(content)
            print("-" * 40)
            print("\n📊 性能统计：")
            print(f"- 耗时: {duration:.2f} 秒")
            print(f"- Prompt Tokens: {prompt_tokens}")
            print(f"- Completion Tokens: {completion_tokens}")
            print(f"- Total Tokens: {total_tokens}")
            print(f"- 生成速度: {tps:.2f} tokens/s")

    except urllib.error.URLError as e:
        print(f"❌ 网络请求失败: {e}")
        if hasattr(e, 'reason'):
            print(f"  原因: {e.reason}")
        if hasattr(e, 'code'):
            print(f"  HTTP 状态码: {e.code}")
    except Exception as e:
        print(f"❌ 发生未知错误: {str(e)}")

if __name__ == "__main__":
    test_llm_request()
