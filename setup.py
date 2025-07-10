#!/usr/bin/env python3
"""
支持热词预测的语音识别系统 - 初始化设置脚本
作者：李俊洁 (项目组长)
日期：2025年7月8日

此脚本用于初始化系统环境，包括：
1. 检查并安装Python和Node.js依赖
2. 配置数据库
3. 创建必要的目录结构
4. 生成默认配置文件
"""

import os
import sys
import subprocess
import shutil
import secrets
from pathlib import Path

class ASRSystemSetup:
    def __init__(self):
        self.project_root = Path(__file__).parent.absolute()
        self.backend_dir = self.project_root / "asr_system_backend"
        self.frontend_dir = self.project_root / "asr_system_frontend"
        
    def print_banner(self):
        """显示设置横幅"""
        print("=" * 60)
        print("    支持热词预测的语音识别系统")
        print("    ASR System with Hotword Prediction")
        print("=" * 60)
        print("正在初始化系统环境...\n")
        
    def check_prerequisites(self):
        """检查系统先决条件"""
        print("🔍 检查系统先决条件...")
        
        # 检查Python版本
        python_version = sys.version_info
        if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
            print("❌ 错误：需要Python 3.8或更高版本")
            return False
        print(f"✅ Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
        
        # 检查Node.js
        try:
            result = subprocess.run(['node', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Node.js版本: {result.stdout.strip()}")
            else:
                print("❌ 错误：未找到Node.js，请先安装Node.js")
                return False
        except FileNotFoundError:
            print("❌ 错误：未找到Node.js，请先安装Node.js")
            return False
        
        # 检查npm
        try:
            result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ npm版本: {result.stdout.strip()}")
            else:
                print("❌ 错误：未找到npm")
                return False
        except FileNotFoundError:
            print("❌ 错误：未找到npm")
            return False
            
        return True

if __name__ == "__main__":
    setup = ASRSystemSetup()
    setup.print_banner()
    if setup.check_prerequisites():
        print("✅ 系统先决条件检查通过")
        print("请运行完整的构建脚本: python -m build 或使用 build.sh")
    else:
        print("❌ 系统先决条件检查失败")
        sys.exit(1) 