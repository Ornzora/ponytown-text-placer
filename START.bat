@echo off
setlocal
cd /d "%~dp0"
title PonyTown Text Placer

set "PY="
py -3 -c "import sys; sys.exit(sys.version_info < (3, 10))" >nul 2>nul && set "PY=py -3"
if not defined PY python -c "import sys; sys.exit(sys.version_info < (3, 10))" >nul 2>nul && set "PY=python"

if not defined PY (
    echo Python 3.10 or newer was not found.
    echo Python 3.10 atau lebih baru tidak ditemukan.
    echo.
    echo Install it from https://www.python.org/downloads/windows/ and enable "Add Python to PATH".
    echo.
    pause
    exit /b 1
)

%PY% -c "import tkinter" >nul 2>nul
if errorlevel 1 (
    echo Tkinter is missing. Reinstall Python and keep "tcl/tk and IDLE" selected.
    echo Tkinter tidak ditemukan. Instal ulang Python dan pilih "tcl/tk and IDLE".
    echo.
    pause
    exit /b 1
)

%PY% -c "import pyautogui, pynput, PIL" >nul 2>nul
if errorlevel 1 (
    echo Installing dependencies...
    echo Memasang dependensi...
    echo.
    %PY% -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo Failed to install dependencies. Check your internet connection and try again.
        echo Gagal memasang dependensi. Periksa koneksi internet lalu coba lagi.
        echo.
        pause
        exit /b 1
    )
)

%PY% pony_town_text_placer.py
if errorlevel 1 (
    echo.
    echo The app closed with an error. See the message above.
    echo Aplikasi tertutup karena error. Lihat pesan di atas.
    pause
)
endlocal
