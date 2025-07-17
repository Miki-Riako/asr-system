import requests
import json
import os
import time

# 配置
API_BASE = "http://localhost:8080/api"
TEST_AUDIO = "client/BAC009S0764W0179.wav"
TEST_USER = {
    "username": "testuser",
    "password": "testpass123"
}

def register_user():
    """注册测试用户"""
    try:
        response = requests.post(f"{API_BASE}/auth/register", json=TEST_USER)
        print("注册结果:", response.json())
    except:
        print("用户可能已存在,继续登录")

def login():
    """登录并获取token"""
    response = requests.post(f"{API_BASE}/auth/login", data=TEST_USER)
    return response.json()["access_token"]

def upload_and_transcribe(token):
    """上传音频并获取转写结果"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # 上传文件
    print("正在上传音频文件...")
    with open(TEST_AUDIO, "rb") as f:
        files = {"file": (os.path.basename(TEST_AUDIO), f)}
        response = requests.post(
            f"{API_BASE}/asr/transcribe/file",
            headers=headers,
            files=files
        )
        
        if not response.ok:
            print("上传失败:", response.text)
            return
            
        task_id = response.json()["id"]
        print(f"上传成功,任务ID: {task_id}")
    
    # 等待处理完成并获取结果
    print("等待转写完成...")
    time.sleep(2)  # 给一些处理时间
    
    response = requests.get(
        f"{API_BASE}/asr/tasks/{task_id}/output",
        headers=headers
    )
    
    if response.ok:
        result = response.json()
        print("\n转写结果:")
        print("-" * 50)
        print(result["terminal_output"])
        print("-" * 50)
    else:
        print("获取结果失败:", response.text)

def main():
    print("开始测试转写功能...")
    register_user()
    token = login()
    upload_and_transcribe(token)

if __name__ == "__main__":
    main() 