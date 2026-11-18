@echo off
setlocal
cd /d "%~dp0"
if errorlevel 1 goto DirectoryError

set "APP_EXE=%~dp0SGHU_Universidad_Windows.exe"
if not exist "%APP_EXE%" goto ExecutableError

echo Abriendo Sistema de Horarios Universitarios...
"%APP_EXE%"
if errorlevel 1 (
    echo.
    echo [ERROR] La aplicacion termino con un error.
    pause
    exit /b 1
)
exit /b 0

:DirectoryError
echo [ERROR] No se pudo acceder a la carpeta del sistema.
goto Failed

:ExecutableError
echo [ERROR] No se encontro SGHU_Universidad_Windows.exe en esta carpeta.
echo Descargue y extraiga el paquete Windows completo antes de ejecutar este archivo.
goto Failed

:Failed
pause
exit /b 1
