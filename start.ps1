# 智能简历管理系统 - 启动脚本 (Windows PowerShell)
# 使用方法: 右键 -> 使用 PowerShell 运行，或在终端中执行 .\start.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    智能简历管理系统 - 启动脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$projectRoot = $PSScriptRoot
$backendDir = "$projectRoot\backend"
$frontendDir = "$projectRoot\frontend"

# Check Python
Write-Host "[1/6] 检查 Python 环境..." -ForegroundColor Yellow
$pythonCmd = $null
foreach ($cmd in @("python", "python3", "py")) {
    try {
        $ver = & $cmd --version 2>&1
        if ($ver -match "Python 3") {
            $pythonCmd = $cmd
            Write-Host "  找到: $ver" -ForegroundColor Green
            break
        }
    } catch { }
}
if (-not $pythonCmd) {
    Write-Host "  错误: 未找到 Python 3，请先安装 Python 3.9+" -ForegroundColor Red
    exit 1
}

# Check Node.js
Write-Host "[2/6] 检查 Node.js 环境..." -ForegroundColor Yellow
$nodeVer = & node --version 2>&1
Write-Host "  Node.js: $nodeVer" -ForegroundColor Green

# Create venv if needed
Write-Host "[3/6] 准备 Python 虚拟环境..." -ForegroundColor Yellow
if (-not (Test-Path "$backendDir\venv")) {
    & $pythonCmd -m venv "$backendDir\venv"
    Write-Host "  虚拟环境已创建" -ForegroundColor Green
} else {
    Write-Host "  虚拟环境已存在" -ForegroundColor Green
}

# Activate venv and install deps
Write-Host "[4/6] 安装后端依赖..." -ForegroundColor Yellow
& "$backendDir\venv\Scripts\pip.exe" install -r "$backendDir\requirements.txt" --quiet

# Copy .env if needed
if (-not (Test-Path "$backendDir\.env")) {
    Copy-Item "$backendDir\.env.example" "$backendDir\.env"
    Write-Host "  已创建 .env 文件（请根据需要修改配置）" -ForegroundColor Green
}

# Run migrations
Write-Host "[5/6] 数据库迁移和初始化..." -ForegroundColor Yellow
Push-Location $backendDir
& "$backendDir\venv\Scripts\python.exe" manage.py makemigrations users resumes ai_assistant 2>&1 | Out-Null
& "$backendDir\venv\Scripts\python.exe" manage.py migrate 2>&1 | Out-Null
& "$backendDir\venv\Scripts\python.exe" manage.py init_data 2>&1
Pop-Location

# Install frontend deps
Write-Host "[6/6] 安装前端依赖..." -ForegroundColor Yellow
if (-not (Test-Path "$frontendDir\node_modules")) {
    Push-Location $frontendDir
    npm install --silent
    Pop-Location
    Write-Host "  前端依赖已安装" -ForegroundColor Green
} else {
    Write-Host "  前端依赖已存在" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "    启动服务" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Start backend
Write-Host "启动 Django 后端 (端口 8000)..." -ForegroundColor Cyan
$backendProcess = Start-Process -FilePath "$backendDir\venv\Scripts\python.exe" -ArgumentList "manage.py runserver 0.0.0.0:8000" -WorkingDirectory $backendDir -PassThru -WindowStyle Normal

# Start frontend
Write-Host "启动 Vue3 前端 (端口 5173)..." -ForegroundColor Cyan
$frontendProcess = Start-Process -FilePath "npm" -ArgumentList "run dev" -WorkingDirectory $frontendDir -PassThru -WindowStyle Normal

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  后端地址: http://localhost:8000" -ForegroundColor White
Write-Host "  前端地址: http://localhost:5173" -ForegroundColor White
Write-Host "  管理后台: http://localhost:8000/admin/" -ForegroundColor White
Write-Host "  API文档: http://localhost:8000/api/" -ForegroundColor White
Write-Host "" -ForegroundColor White
Write-Host "  管理员账号: admin / admin123" -ForegroundColor Yellow
Write-Host "  普通用户: zhangsan / user123" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "按 Ctrl+C 退出..." -ForegroundColor Gray
try { $backendProcess.WaitForExit() } catch { }
