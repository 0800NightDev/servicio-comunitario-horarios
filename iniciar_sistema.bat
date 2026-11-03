@echo off
cd /d "%~dp0"
title Sistema de Organizacion de Horarios Universitarios (Servicio Comunitario)
echo Abriendo interfaz grafica del Sistema de Horarios Universitarios...
.\.venv\Scripts\python.exe SGHU_Universidad.py
pause
