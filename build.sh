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
npm install
cd ..

# 运行数据库迁移
echo -e "${GREEN}>>> 初始化数据库...${NC}"
cd asr_system_backend
python -c "
from app.database import Base, engine
Base.metadata.create_all(bind=engine)
"
export PYTHONPATH=$PYTHONPATH:$(pwd)
alembic upgrade head
cd ..

echo -e "${BLUE}=== 构建完成! ===${NC}"
echo -e "${BLUE}=== 使用 run.sh 来启动应用 ===${NC}" 