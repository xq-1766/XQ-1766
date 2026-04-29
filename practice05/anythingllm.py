import os
import subprocess
import json
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def anythingllm_query(message):
    """
    使用 subprocess 调用 curl 访问 AnythingLLM API
    """
    api_key = os.getenv("ANYTHINGLLM_API_KEY")
    workspace_slug = os.getenv("ANYTHINGLLM_WORKSPACE_SLUG")
    
    if not api_key or not workspace_slug:
        return json.dumps({"error": "ANYTHINGLLM_API_KEY or ANYTHINGLLM_WORKSPACE_SLUG not found in .env"})

    url = f"http://localhost:3001/api/v1/workspace/{workspace_slug}/chat"
    
    # 构造请求数据，确保中文不被转义
    data = json.dumps({"message": message, "mode": "chat"}, ensure_ascii=False)
    
    # 构造 curl 命令
    cmd = [
        "curl",
        "-s", # 静默模式，不显示进度
        "-X", "POST",
        url,
        "-H", f"Authorization: Bearer {api_key}",
        "-H", "Content-Type: application/json",
        "-d", data
    ]
    
    try:
        # 执行命令，捕获输出
        # 注意：在 Windows 上，curl 可能需要显式指定编码，或者确保 Python 环境处理好编码
        # 我们这里使用 subprocess.run 并设置 encoding='utf-8'
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode != 0:
            return json.dumps({"error": f"Curl command failed: {result.stderr}"})
        
        # 解析返回的 JSON
        try:
            response_json = json.loads(result.stdout)
            # AnythingLLM 的返回通常包含 'textResponse'
            return json.dumps(response_json, ensure_ascii=False)
        except json.JSONDecodeError:
            return json.dumps({"error": "Failed to decode JSON response", "raw": result.stdout}, ensure_ascii=False)
            
    except Exception as e:
        return json.dumps({"error": f"An error occurred: {str(e)}"}, ensure_ascii=False)

if __name__ == "__main__":
    # 简单测试
    print(anythingllm_query("你好，请介绍一下你自己"))
