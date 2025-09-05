@echo off
echo ========================================
echo 艺术品推荐系统启动脚本
echo ========================================
echo.

echo 1. 启动后端服务...
cd backend
start "后端服务" cmd /k "python main.py"
echo 后端服务正在启动，请等待...
timeout /t 3 /nobreak >nul

echo.
echo 2. 启动前端服务...
cd ..\frontend
start "前端服务" cmd /k "python server.py"
echo 前端服务正在启动...
timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo 启动完成！
echo 后端服务: http://localhost:8000
echo 前端服务: http://localhost:3000
echo ========================================
echo.
echo 按任意键关闭此窗口...
pause >nul
