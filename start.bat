@echo off
chcp 65001 >nul
echo Starting AI Gateway Development Environment...

echo.
echo 1. Stopping existing containers...
docker-compose -f docker-compose.dev.yml down

echo.
echo 2. Starting development environment...
docker-compose -f docker-compose.dev.yml up -d

echo.
echo 3. Waiting for services to start...
timeout /t 20 /nobreak > nul

echo.
echo 4. Showing service status...
docker-compose -f docker-compose.dev.yml ps

echo.
echo Development environment started!
echo.
echo Getting frontend port...
for /f "tokens=2" %%i in ('docker port ai-gateway-frontend-dev 3000') do set FRONTEND_PORT=%%i
echo Frontend: http://localhost:%FRONTEND_PORT%
echo Backend API: http://localhost:8001
echo Mock LLM: http://localhost:8003
echo Database: localhost:3307
echo Redis: localhost:6379
echo.
echo Code is mounted to containers, changes will auto-reload!
echo.
echo View logs:
echo Frontend: docker-compose -f docker-compose.dev.yml logs -f frontend
echo Backend: docker-compose -f docker-compose.dev.yml logs -f config-center
echo.
echo Press any key to exit...
pause > nul
