@echo off
echo Iniciando o sistema de reservas de viagem...

REM Iniciar o backend Spring Boot
echo Iniciando o backend Spring Boot...
start cmd /k "cd chatbot-api && mvnw spring-boot:run"

REM Aguardar o backend iniciar
echo Aguardando o backend inicializar (15 segundos)...
timeout /t 15 /nobreak

REM Iniciar o bot Python
echo Iniciando o chatbot...
start cmd /k "cd bot-reserva && python app.py"

echo.
echo Sistema iniciado! Abra o Bot Framework Emulator e conecte-se a:
echo http://localhost:3979/api/messages
echo.