@echo off
chcp 65001 >nul
echo ========================================
echo 🚀 浏览器远程控制系统启动脚本
echo ========================================
echo.
echo 请按顺序执行以下步骤：
echo.
echo 1. 首先启动WebSocket服务器
echo 2. 然后在浏览器中安装插件
echo 3. 最后启动GUI控制界面
echo.
echo ========================================
echo.

:menu
echo 请选择操作：
echo [1] 启动WebSocket服务器
echo [2] 启动GUI控制界面
echo [3] 安装Python依赖
echo [4] 退出
echo.
set /p choice=请输入选项 (1-4): 

if "%choice%"=="1" goto server
if "%choice%"=="2" goto gui
if "%choice%"=="3" goto install
if "%choice%"=="4" goto end
echo 无效选项，请重新选择
echo.
goto menu

:install
echo.
echo 正在安装Python依赖...
pip install -r requirements.txt
echo.
echo 依赖安装完成！
echo.
pause
goto menu

:server
echo.
echo 正在启动WebSocket服务器...
echo.
python server.py
goto menu

:gui
echo.
echo 正在启动GUI控制界面...
echo.
python gui.py
goto menu

:end
echo.
echo 再见！
exit

