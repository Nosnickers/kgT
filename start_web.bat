@echo off
chcp 65001 >nul
echo ====================================
echo 知识图谱问答系统 Web 服务
echo ====================================
echo.

echo [1/3] 检查虚拟环境...
if not exist "venv\Scripts\activate.bat" (
    echo 错误: 虚拟环境不存在，请先创建虚拟环境
    echo 运行: python -m venv venv
    pause
    exit /b 1
)

echo [2/3] 激活虚拟环境...
call venv\Scripts\activate.bat

echo [3/3] 检查依赖...
pip show flask >nul 2>&1
if errorlevel 1 (
    echo Flask 未安装，正在安装依赖...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo 错误: 依赖安装失败
        pause
        exit /b 1
    )
)

echo.
echo ====================================
echo 启动 Web 服务器...
echo ====================================
echo.
echo 服务将在 http://localhost:5000 启动
echo 按 Ctrl+C 停止服务
echo.

python web_server.py

pause
