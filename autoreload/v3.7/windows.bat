@echo off
REM SPDX-License-Identifier: AGPL-3.0-only

if not exist autoreload_venv (
  echo Venv not found! Creating venv...
  python -m venv autoreload_venv || goto :error
)

echo Activating venv...
call autoreload_venv\Scripts\activate.bat || goto :error

pip install -r requirements.txt --upgrade-strategy only-if-needed || goto :error

echo Starting main.py...

:loop
python main.py >> autoreload.log 2>&1
goto loop

:error
echo error!
pause
