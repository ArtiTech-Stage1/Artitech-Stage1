#!/bin/bash

echo "========================================"
echo "艺术品推荐系统启动脚本"
echo "========================================"
echo

echo "1. 启动后端服务..."
cd backend
python main.py &
BACKEND_PID=$!
echo "后端服务已启动 (PID: $BACKEND_PID)"
sleep 3

echo
echo "2. 启动前端服务..."
cd ../frontend
python server.py &
FRONTEND_PID=$!
echo "前端服务已启动 (PID: $FRONTEND_PID)"
sleep 2

echo
echo "========================================"
echo "启动完成！"
echo "后端服务: http://localhost:8000"
echo "前端服务: http://localhost:3000"
echo "========================================"
echo
echo "按 Ctrl+C 停止所有服务"

# 等待用户中断
trap "echo '正在停止服务...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
