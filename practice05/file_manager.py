import os
import json
import requests
import re
def get_url_content(url, timeout=30):
    """
    通过网络访问获取网页内容。
    """
    if not url:
        return json.dumps({"error": "URL is required."})
    
    # 彻底清理 URL：去除所有空格、换行、引号、反引号
    clean_url = re.sub(r'[\s`\'"]', '', url)
    
    # 针对 wttr.in 的优化：如果用户没有指定格式，自动加上 ?format=2
    # format=2 提供更丰富但依然简洁的文本格式，包含温度、天气、风速、湿度等
    if "wttr.in" in clean_url and "?" not in clean_url:
        clean_url += "?format=2"

    # 模拟 curl 请求头
    headers = {
        "User-Agent": "curl/7.64.1",
        "Accept-Language": "zh-CN,zh;q=0.9"
    }
    
    # 增加重试机制
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            response = requests.get(clean_url, headers=headers, timeout=timeout)
            # 强制使用 utf-8 编码，防止中文乱码
            response.encoding = 'utf-8'
            response.raise_for_status()
            
            # 如果是 wttr.in，去掉可能存在的 ANSI 转义字符（颜色代码）
            content = response.text.strip()
            if "wttr.in" in clean_url:
                content = re.sub(r'\x1b\[[0-9;]*[mGKF]', '', content)
                
            return json.dumps({"content": content}, ensure_ascii=False)
        except requests.exceptions.Timeout:
            if attempt < max_retries:
                continue
            return json.dumps({"error": f"The request timed out after {timeout}s."}, ensure_ascii=False)
        except requests.exceptions.RequestException as e:
            if attempt < max_retries:
                continue
            return json.dumps({"error": f"Failed to fetch URL: {str(e)}"}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": f"An unexpected error occurred: {str(e)}"}, ensure_ascii=False)
def list_directory_contents(path):
    """
    列出指定目录下的文件和子目录，包括它们的基本属性和大小。
    """
    if not os.path.isdir(path):
        return json.dumps({"error": f"Path '{path}' is not a directory."})

    contents = []
    for item in os.listdir(path):
        item_path = os.path.join(path, item)
        item_info = {
            "name": item,
            "path": item_path,
            "is_directory": os.path.isdir(item_path),
            "size": os.path.getsize(item_path) if os.path.isfile(item_path) else None,
            "last_modified": os.path.getmtime(item_path)
        }
        contents.append(item_info)
    return json.dumps({"contents": contents})

def rename_file(directory_path, old_name, new_name):
    """
    重命名指定目录下的文件。
    """
    old_file_path = os.path.join(directory_path, old_name)
    new_file_path = os.path.join(directory_path, new_name)

    if not os.path.exists(old_file_path):
        return json.dumps({"error": f"File '{old_name}' not found in '{directory_path}'."})
    if os.path.exists(new_file_path):
        return json.dumps({"error": f"File or directory with name '{new_name}' already exists in '{directory_path}'."})

    try:
        os.rename(old_file_path, new_file_path)
        return json.dumps({"success": f"File '{old_name}' renamed to '{new_name}'."})
    except Exception as e:
        return json.dumps({"error": f"Failed to rename file: {e}"})

def delete_file(directory_path, file_name):
    """
    删除指定目录下的文件。
    """
    file_path = os.path.join(directory_path, file_name)

    if not os.path.exists(file_path):
        return json.dumps({"error": f"File '{file_name}' not found in '{directory_path}'."})
    if os.path.isdir(file_path):
        return json.dumps({"error": f"'{file_name}' is a directory, not a file. Use a different tool to remove directories."})

    try:
        os.remove(file_path)
        return json.dumps({"success": f"File '{file_name}' deleted from '{directory_path}'."})
    except Exception as e:
        return json.dumps({"error": f"Failed to delete file: {e}"})

def create_write_file(directory_path, file_name, content):
    """
    在指定目录下创建文件并写入内容。
    """
    file_path = os.path.join(directory_path, file_name)

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return json.dumps({"success": f"File '{file_name}' created and content written in '{directory_path}'."})
    except Exception as e:
        return json.dumps({"error": f"Failed to create or write to file: {e}"})

def read_file_content(directory_path, file_name):
    """
    读取指定目录下的文件的内容。
    """
    file_path = os.path.join(directory_path, file_name)

    if not os.path.exists(file_path):
        return json.dumps({"error": f"File '{file_name}' not found in '{directory_path}'."})
    if os.path.isdir(file_path):
        return json.dumps({"error": f"'{file_name}' is a directory, not a file."})

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return json.dumps({"content": content})
    except Exception as e:
        return json.dumps({"error": f"Failed to read file: {e}"})
