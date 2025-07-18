#!/bin/bash

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# 端口配置
BACKEND_PORT=${BACKEND_PORT:-8080}
FRONTEND_PORT=${FRONTEND_PORT:-2956}
EDITOR_PORT=8765 # <-- 新增：编辑器的端口

# PID文件
BACKEND_PID_FILE=".backend.pid"
FRONTEND_PID_FILE=".frontend.pid"
EDITOR_PID_FILE=".editor.pid" # <-- 新增：编辑器的PID文件

# 检查并清理被占用的端口
check_and_clean_port() {
    local port=$1
    local name=$2
    local pid=$(lsof -ti:${port})
    if [ ! -z "$pid" ]; then
        echo -e "${YELLOW}端口 ${port} (${name}) 被进程 ${pid} 占用，正在清理...${NC}"
        kill -9 $pid
        sleep 1
    fi
}

start_services() {
    echo -e "${BLUE}=== 支持热词预测的语音识别系统启动脚本 ===${NC}"
    
    # 检查并清理端口
    check_and_clean_port $BACKEND_PORT "Backend"
    check_and_clean_port $FRONTEND_PORT "Frontend"
    check_and_clean_port $EDITOR_PORT "Editor" # <-- 新增：检查编辑器端口
    
    # 检查是否已经运行
    if [ -f "$BACKEND_PID_FILE" ] || [ -f "$FRONTEND_PID_FILE" ] || [ -f "$EDITOR_PID_FILE" ]; then
        echo -e "${RED}服务似乎已在运行，请先运行 ./run.sh stop 停止服务。${NC}"
        return 1
    fi
    
    # 启动后端服务
    echo -e "${GREEN}>>> 启动后端服务...${NC}"
    cd asr_system_backend
    nohup uvicorn app.main:app --reload --host 0.0.0.0 --port $BACKEND_PORT > ../backend.log 2>&1 &
    echo $! > ../$BACKEND_PID_FILE
    cd ..
    
    # 启动前端服务
    echo -e "${GREEN}>>> 启动前端服务...${NC}"
    cd asr_system_frontend
    nohup npm run dev -- --port $FRONTEND_PORT --host > ../frontend.log 2>&1 &
    echo $! > ../$FRONTEND_PID_FILE
    cd ..

    # <-- 新增：启动独立的热词编辑器服务 -->
    echo -e "${GREEN}>>> 启动热词编辑器服务...${NC}"
    nohup python hotword_editor.py > editor.log 2>&1 &
    echo $! > $EDITOR_PID_FILE
    # <-- 新增结束 -->
    
    echo -e "${BLUE}=== 所有服务已启动! ===${NC}"
    echo -e "${GREEN}前端主应用: ${YELLOW}http://localhost:$FRONTEND_PORT${NC}"
    echo -e "${GREEN}热词编辑器: ${YELLOW}http://localhost:$EDITOR_PORT${NC}"
    echo -e "${GREEN}后端API文档: ${YELLOW}http://localhost:$BACKEND_PORT/docs${NC}"
    echo -e "${BLUE}=============================${NC}"
    echo -e "${BLUE}=== 使用 ./run.sh logs 查看日志 ===${NC}"
    echo -e "${BLUE}=== 使用 ./run.sh stop 停止服务 ===${NC}"
}

stop_services() {
    echo -e "${BLUE}=== 正在停止所有服务... ===${NC}"
    
    # 停止后端
    if [ -f "$BACKEND_PID_FILE" ]; then
        kill $(cat $BACKEND_PID_FILE) 2>/dev/null
        rm $BACKEND_PID_FILE
        echo -e "${GREEN}>>> 后端服务已停止。${NC}"
    fi
    
    # 停止前端
    if [ -f "$FRONTEND_PID_FILE" ]; then
        kill $(cat $FRONTEND_PID_FILE) 2>/dev/null
        rm $FRONTEND_PID_FILE
        echo -e "${GREEN}>>> 前端服务已停止。${NC}"
    fi

    # <-- 新增：停止编辑器服务 -->
    if [ -f "$EDITOR_PID_FILE" ]; then
        kill $(cat $EDITOR_PID_FILE) 2>/dev/null
        rm $EDITOR_PID_FILE
        echo -e "${GREEN}>>> 热词编辑器服务已停止。${NC}"
    fi
    # <-- 新增结束 -->
    
    echo -e "${BLUE}=== 所有服务已停止 ===${NC}"
}

show_logs() {
    echo -e "${BLUE}=== 显示所有日志 (按 Ctrl+C 退出) ===${NC}"
    tail -f backend.log frontend.log editor.log
}

# 主命令处理
case $1 in
    stop)
        stop_services
        ;;
    logs)
        show_logs
        ;;
    *)
        start_services
        ;;
esac