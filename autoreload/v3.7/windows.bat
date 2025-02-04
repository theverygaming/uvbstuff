@echo off
if not exist autoreload_venv python -m venv autoreload_venv || goto :error
call autoreload_venv\Scripts\activate.bat || goto :error
pip install git+https://github.com/theverygaming/silly.git@050482f272af4fab564c15238bd7b17ecf22197d || goto :error
pip install requests

:loop
python main.py >> autoreload.log 2>&1
goto loop

:error
echo error!
pause
