#!/usr/bin/env python3
"""
系统功能验证脚本
用于快速检查ASR系统的各项功能是否正常工作
"""

import os
import sys
import time
import requests
import json
from pathlib import Path

class SystemVerifier:
    def __init__(self):
        self.base_url = "http://localhost:8080"
        self.frontend_url = "http://localhost:2956"
        self.token = None
        self.test_user = {
            "username": "test_user_" + str(int(time.time())),
            "password": "test123456"
        }
    
    def print_banner(self):
        print("=" * 60)
        print("     ASR系统功能验证")
        print("=" * 60)
        print()
    
    def check_backend_health(self):
        """检查后端服务是否正常运行"""
        print("🔍 检查后端服务健康状态...")
        try:
            response = requests.get(f"{self.base_url}/docs", timeout=5)
            if response.status_code == 200:
                print("✅ 后端服务运行正常")
                return True
            else:
                print("❌ 后端服务响应异常")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ 无法连接到后端服务: {e}")
            print("请确保后端服务已启动 (运行 ./run.sh 或 .\run.ps1)")
            return False
    
    def check_frontend_health(self):
        """检查前端服务是否正常运行"""
        print("🔍 检查前端服务健康状态...")
        try:
            response = requests.get(self.frontend_url, timeout=5)
            if response.status_code == 200:
                print("✅ 前端服务运行正常")
                return True
            else:
                print("❌ 前端服务响应异常")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ 无法连接到前端服务: {e}")
            print("请确保前端服务已启动")
            return False
    
    def test_user_registration(self):
        """测试用户注册功能"""
        print("🔍 测试用户注册功能...")
        try:
            response = requests.post(
                f"{self.base_url}/auth/register",
                json=self.test_user,
                timeout=10
            )
            if response.status_code == 200:
                print("✅ 用户注册功能正常")
                return True
            else:
                print(f"❌ 用户注册失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 用户注册测试失败: {e}")
            return False
    
    def test_user_login(self):
        """测试用户登录功能"""
        print("🔍 测试用户登录功能...")
        try:
            # 准备表单数据格式
            login_data = {
                "username": self.test_user["username"],
                "password": self.test_user["password"]
            }
            
            response = requests.post(
                f"{self.base_url}/auth/login",
                data=login_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if "access_token" in result:
                    self.token = result["access_token"]
                    print("✅ 用户登录功能正常")
                    return True
                else:
                    print("❌ 登录响应中缺少token")
                    return False
            else:
                print(f"❌ 用户登录失败: {response.status_code}")
                print(f"响应内容: {response.text}")
                return False
        except Exception as e:
            print(f"❌ 用户登录测试失败: {e}")
            return False
    
    def test_hotword_management(self):
        """测试热词管理功能"""
        print("🔍 测试热词管理功能...")
        if not self.token:
            print("❌ 需要先登录才能测试热词管理")
            return False
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            # 测试创建热词
            hotword_data = {"word": "测试热词", "weight": 8}
            response = requests.post(
                f"{self.base_url}/hotwords",
                json=hotword_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                hotword = response.json()
                hotword_id = hotword["id"]
                
                # 测试获取热词列表
                response = requests.get(
                    f"{self.base_url}/hotwords",
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    hotwords = response.json()
                    if len(hotwords) > 0:
                        print("✅ 热词管理功能正常")
                        
                        # 清理测试数据
                        requests.delete(
                            f"{self.base_url}/hotwords/{hotword_id}",
                            headers=headers
                        )
                        return True
                    else:
                        print("❌ 热词列表为空")
                        return False
                else:
                    print("❌ 获取热词列表失败")
                    return False
            else:
                print(f"❌ 创建热词失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 热词管理测试失败: {e}")
            return False
    
    def test_transcription_api(self):
        """测试转写API（不上传真实文件）"""
        print("🔍 测试转写API端点...")
        if not self.token:
            print("❌ 需要先登录才能测试转写API")
            return False
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            # 测试获取任务列表API
            response = requests.get(
                f"{self.base_url}/asr/tasks",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ 转写API端点正常")
                return True
            else:
                print(f"❌ 转写API测试失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 转写API测试失败: {e}")
            return False
    
    def check_database(self):
        """检查数据库连接"""
        print("🔍 检查数据库连接...")
        try:
            # 检查数据库文件是否存在
            db_path = Path("asr_system_backend/asr_system.db")
            if db_path.exists():
                print("✅ 数据库文件存在")
                return True
            else:
                print("❌ 数据库文件不存在")
                print("请运行数据库初始化: cd asr_system_backend && python init_db.py")
                return False
        except Exception as e:
            print(f"❌ 数据库检查失败: {e}")
            return False
    
    def check_required_files(self):
        """检查必要文件是否存在"""
        print("🔍 检查必要文件...")
        
        required_files = [
            "asr_system_backend/app/main.py",
            "asr_system_backend/app/models.py",
            "asr_system_backend/app/asr_engine.py",
            "asr_system_backend/app/rag_service.py",
            "asr_system_frontend/src/main.js",
            "asr_system_frontend/src/App.vue",
        ]
        
        all_exist = True
        for file_path in required_files:
            if Path(file_path).exists():
                print(f"✅ {file_path}")
            else:
                print(f"❌ {file_path} 缺失")
                all_exist = False
        
        return all_exist
    
    def print_summary(self, results):
        """打印测试结果摘要"""
        print("\n" + "=" * 60)
        print("     测试结果摘要")
        print("=" * 60)
        
        passed = sum(results.values())
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{test_name:<20} {status}")
        
        print("-" * 60)
        print(f"总计: {passed}/{total} 项测试通过")
        
        if passed == total:
            print("\n🎉 所有测试通过！系统运行正常！")
            print("\n🚀 您现在可以：")
            print("   - 访问前端界面: http://localhost:2956")
            print("   - 查看API文档: http://localhost:8080/docs")
            print("   - 开始使用语音识别功能")
        else:
            print(f"\n⚠️  有 {total - passed} 项测试失败，请检查相关组件")
    
    def run_all_tests(self):
        """运行所有测试"""
        self.print_banner()
        
        results = {}
        
        # 基础环境检查
        results["必要文件检查"] = self.check_required_files()
        results["数据库检查"] = self.check_database()
        results["后端服务"] = self.check_backend_health()
        results["前端服务"] = self.check_frontend_health()
        
        # 功能测试（只有在服务正常时才执行）
        if results["后端服务"]:
            results["用户注册"] = self.test_user_registration()
            results["用户登录"] = self.test_user_login()
            results["热词管理"] = self.test_hotword_management()
            results["转写API"] = self.test_transcription_api()
        
        self.print_summary(results)
        
        return all(results.values())

def main():
    verifier = SystemVerifier()
    success = verifier.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 