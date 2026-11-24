@echo off
rem REASON O1 / VIBECODING - abre o painel no browser
cd /d "%~dp0"
where python >nul 2>nul && (python reason_o1.py & goto :eof)
where py >nul 2>nul && (py -3 reason_o1.py & goto :eof)
echo Precisas do Python 3.10 ou mais recente: https://www.python.org/downloads/
pause
