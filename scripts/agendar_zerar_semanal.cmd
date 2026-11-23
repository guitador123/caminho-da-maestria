@echo off
setlocal
chcp 65001 >nul 2>&1
title Agendar - Zerar missoes semanais

REM ============================================================
REM  Agenda a limpeza das missoes semanais de TODAS as contas
REM  Toda quarta-feira as 03h (horario de Brasilia).
REM
REM  Uso:
REM    agendar_zerar_semanal.cmd            cria a tarefa
REM    agendar_zerar_semanal.cmd /testar    testa o script (nao altera nada)
REM    agendar_zerar_semanal.cmd /remover   apaga a tarefa
REM ============================================================

set "AQUI=%~dp0"
set "SCRIPT=%AQUI%zerar_semanais_semanal.py"
set "TAREFA=Caminho da Maestria - Zerar missoes semanais"
set "CHAVE=%LOCALAPPDATA%\Caminho da Maestria\service_role.txt"

if /i "%~1"=="/remover" goto :remover
if /i "%~1"=="/testar" goto :testar

echo.
echo  =====================================================
echo   Agendar a limpeza semanal das missoes
echo  =====================================================
echo.
echo   Quando: toda QUARTA-FEIRA as 03:00
echo   (o horario do Windows nesta maquina e Brasilia / UTC-3)
echo.
echo   O que faz: marca como "Falso" as 7 missoes semanais
echo   de todas as contas do Supabase.
echo.

REM ---- procura um Python de verdade (ignora o stub da Microsoft Store) ---
set "PYTHON="
for /f "delims=" %%I in ('where python 2^>nul') do (
    if not defined PYTHON (
        echo %%I | find /i "WindowsApps" >nul || set "PYTHON=%%I"
    )
)
if not defined PYTHON (
    for /f "delims=" %%I in ('where py 2^>nul') do (
        if not defined PYTHON set "PYTHON=%%I"
    )
)
if not defined PYTHON (
    echo  ERRO: nao achei o Python no PATH.
    pause
    exit /b 1
)
echo   Python: %PYTHON%
echo.

REM ---- a chave service_role ---------------------------------------------
if exist "%CHAVE%" goto :criar
echo  AVISO: nao achei a service_role key em:
echo    %CHAVE%
echo.
echo  Sem ela o agendamento falha na hora de rodar. Crie o arquivo
echo  com a chave SOZINHA (painel do Supabase ^> Settings ^> API ^>
echo  Service Role).
echo.
set /p RESP="  Continuar mesmo assim? (S/N): "
if /i "%RESP%"=="S" goto :criar
goto :cancelou

:criar
echo  Criando a tarefa agendada...
schtasks /Create /TN "%TAREFA%" /TR "\"%PYTHON%\" \"%SCRIPT%\"" /SC WEEKLY /D WED /ST 03:00 /F
if errorlevel 1 (
    echo.
    echo  ERRO ao criar a tarefa. Tente como administrador.
    pause
    exit /b 1
)
REM ---- nao depender da energia: roda na bateria tambem -------------------
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$t = Get-ScheduledTask -TaskName '%TAREFA%' -ErrorAction SilentlyContinue; if ($t) { $t.Settings.DisallowStartIfOnBatteries = $false; $t.Settings.StopIfGoingOnBatteries = $false; Set-ScheduledTask -TaskName '%TAREFA%' -Settings $t.Settings | Out-Null }" >nul 2>&1

echo.
echo  =====================================================
echo   Agendado!
echo.
echo   Proxima execucao: quarta-feira as 03:00
echo   Conferir:  schtasks /Query /TN "%TAREFA%"
echo   Remover :  "%AQUI%agendar_zerar_semanal.cmd" /remover
echo  =====================================================
echo.
ping 127.0.0.1 -n 5 >nul
exit /b 0

:testar
echo.
echo  Testando o script (NAO altera nada)...
echo.
"%PYTHON%" "%SCRIPT%" --testar
echo.
pause
exit /b 0

:remover
echo.
echo  Removendo a tarefa agendada...
schtasks /Delete /TN "%TAREFA%" /F
echo.
ping 127.0.0.1 -n 3 >nul
exit /b 0

:cancelou
echo.
echo  Cancelado.
ping 127.0.0.1 -n 3 >nul
exit /b 0
