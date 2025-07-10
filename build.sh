#!/bin/bash

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== 支持热词预测的语音识别系统构建脚本 ===${NC}"
echo -e "${BLUE}=== 开始构建项目... ===${NC}"

# 创建虚拟环境
echo -e "${GREEN}>>> 创建Python虚拟环境...${NC}"
python -m venv venv
source venv/bin/activate

# 创建上传目录
echo -e "${GREEN}>>> 创建必要的目录...${NC}"
mkdir -p asr_system_backend/uploads

# 安装后端依赖
echo -e "${GREEN}>>> 安装后端依赖...${NC}"
cd asr_system_backend
pip install -r requirements.txt
cd ..

# 安装前端依赖
echo -e "${GREEN}>>> 安装前端依赖...${NC}"
cd asr_system_frontend

# 复制环境变量文件（如果不存在）
if [ ! -f ".env" ]; then
    echo -e "${GREEN}>>> 创建前端环境配置文件...${NC}"
    cp env.example .env
    echo -e "${YELLOW}⚠️  请编辑 asr_system_frontend/.env 文件，设置您的配置参数${NC}"
fi

npm install
cd ..

# 运行数据库迁移
echo -e "${GREEN}>>> 初始化数据库...${NC}"
cd asr_system_backend

# 复制环境变量文件（如果不存在）
if [ ! -f ".env" ]; then
    echo -e "${GREEN}>>> 创建后端环境配置文件...${NC}"
    cp env.example .env
    echo -e "${YELLOW}⚠️  请编辑 asr_system_backend/.env 文件，设置您的配置参数${NC}"
fi

# 使用我们的初始化脚本
python init_db.py

# 运行Alembic迁移
export PYTHONPATH=$PYTHONPATH:$(pwd)
alembic upgrade head
cd ..

echo -e "${BLUE}=== 构建完成! ===${NC}"
echo -e "${BLUE}=== 使用 run.sh 来启动应用 ===${NC}" 