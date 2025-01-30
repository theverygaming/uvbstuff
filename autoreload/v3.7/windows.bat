@echo off
if not exist autoreload_venv python -m venv autoreload_venv || goto :error
call autoreload_venv\Scripts\activate.bat || goto :error
pip install git+https://github.com/theverygaming/silly.git@3bac662ed5c7d571e5557e4532aa860a27a45ab4 || goto :error
pip install requests

:loop
python main.py >> autoreload.log 2>&1
goto loop

:error
echo error!
pause
