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
BACKEND_HOST=${BACKEND_HOST:-localhost}

# PID文件
BACKEND_PID_FILE=".backend.pid"
FRONTEND_PID_FILE=".frontend.pid"

# 检查并清理被占用的端口
check_and_clean_port() {
    local port=$1
    local pid=$(lsof -ti:${port})
    if [ ! -z "$pid" ]; then
        echo -e "${YELLOW}端口 ${port} 被进程 ${pid} 占用，正在清理...${NC}"
        kill -9 $pid
        sleep 1
    fi
}

start_services() {
    echo -e "${BLUE}=== 支持热词预测的语音识别系统启动脚本 ===${NC}"
    
    # 检查并清理端口
    check_and_clean_port $BACKEND_PORT
    check_and_clean_port $FRONTEND_PORT
    
    # 检查是否已经运行
    if [ -f "$BACKEND_PID_FILE" ]; then
        echo -e "${RED}后端服务似乎已在运行，请先停止服务。${NC}"
        return 1
    fi
    
    if [ -f "$FRONTEND_PID_FILE" ]; then
        echo -e "${RED}前端服务似乎已在运行，请先停止服务。${NC}"
        return 1
    fi
    
    # 启动后端服务
    echo -e "${GREEN}>>> 启动后端服务...${NC}"
    cd asr_system_backend
    nohup uvicorn app.main:app --reload --host 0.0.0.0 --port $BACKEND_PORT > ../backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > ../$BACKEND_PID_FILE
    cd ..
    
    # 启动前端服务
    echo -e "${GREEN}>>> 启动前端服务...${NC}"
    cd asr_system_frontend
    nohup npm run dev -- --port $FRONTEND_PORT --host > ../frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > ../$FRONTEND_PID_FILE
    cd ..
    
    echo -e "${BLUE}=== 服务已启动! ===${NC}"
    echo -e "${GREEN}后端服务运行于: ${YELLOW}http://localhost:$BACKEND_PORT${NC}"
    echo -e "${GREEN}前端服务运行于: ${YELLOW}http://localhost:$FRONTEND_PORT${NC}"
    echo -e "${GREEN}API文档: ${YELLOW}http://localhost:$BACKEND_PORT/docs${NC}"
    echo -e "${BLUE}=== 使用 ./run.sh logs 查看日志 ===${NC}"
    echo -e "${BLUE}=== 使用 ./run.sh stop 停止服务 ===${NC}"
}

stop_services() {
    echo -e "${BLUE}=== 停止服务... ===${NC}"
    
    # 停止后端
    if [ -f "$BACKEND_PID_FILE" ]; then
        BACKEND_PID=$(cat $BACKEND_PID_FILE)
        echo -e "${GREEN}>>> 停止后端服务 (PID: $BACKEND_PID)...${NC}"
        kill $BACKEND_PID 2>/dev/null || true
        rm $BACKEND_PID_FILE
    else
        echo -e "${YELLOW}未找到后端服务PID文件，服务可能未运行。${NC}"
    fi
    
    # 停止前端
    if [ -f "$FRONTEND_PID_FILE" ]; then
        FRONTEND_PID=$(cat $FRONTEND_PID_FILE)
        echo -e "${GREEN}>>> 停止前端服务 (PID: $FRONTEND_PID)...${NC}"
        kill $FRONTEND_PID 2>/dev/null || true
        rm $FRONTEND_PID_FILE
    else
        echo -e "${YELLOW}未找到前端服务PID文件，服务可能未运行。${NC}"
    fi
    
    echo -e "${BLUE}=== 服务已停止 ===${NC}"
}

show_logs() {
    case $1 in
        backend)
            echo -e "${BLUE}=== 显示后端日志 (按 Ctrl+C 退出) ===${NC}"
            tail -f backend.log
            ;;
        frontend)
            echo -e "${BLUE}=== 显示前端日志 (按 Ctrl+C 退出) ===${NC}"
            tail -f frontend.log
            ;;
        *)
            echo -e "${BLUE}=== 显示所有日志 (按 Ctrl+C 退出) ===${NC}"
            tail -f backend.log frontend.log
            ;;
    esac
}

# 主命令处理
case $1 in
    stop)
        stop_services
        ;;
    logs)
        show_logs $2
        ;;
    *)
        start_services
        ;;
esac 