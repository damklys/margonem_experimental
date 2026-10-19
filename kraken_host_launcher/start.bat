@echo off
rem Kraken - start launchera na Windows: .venv z zaleznosciami (przy pierwszym uruchomieniu) i main_v3.py.
setlocal
cd /d "%~dp0"

set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY (
  where python >nul 2>nul && set "PY=python"
)
if not defined PY (
  echo Brak Pythona 3.10+. Zainstaluj z https://www.python.org/downloads/ ^(zaznacz "Add python.exe to PATH" i "tcl/tk"^).
  pause
  exit /b 1
)
%PY% -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" || (
  echo Potrzebny Python 3.10 lub nowszy.
  pause
  exit /b 1
)
%PY% -c "import tkinter" 2>nul || (
  echo Brak tkinter - zainstaluj Pythona ponownie z opcja "tcl/tk and IDLE".
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Tworze srodowisko .venv...
  %PY% -m venv .venv || ( pause & exit /b 1 )
)
fc /b requirements.txt .venv\.requirements.installed >nul 2>nul || (
  ".venv\Scripts\python.exe" -m pip install --upgrade pip >nul
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt || ( pause & exit /b 1 )
  copy /y requirements.txt .venv\.requirements.installed >nul
)
".venv\Scripts\python.exe" -c "import selenium, undetected_chromedriver, PIL" || ( echo Zaleznosci niezainstalowane poprawnie - usun katalog .venv i uruchom ponownie. & pause & exit /b 1 )
rem pythonw - bez dodatkowego okna konsoli
start "" ".venv\Scripts\pythonw.exe" main_v3.py %*
endlocal
