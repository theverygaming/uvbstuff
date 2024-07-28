@echo off
if not exist autoreload_venv python -m venv autoreload_venv || goto :error
call autoreload_venv\Scripts\activate.bat || goto :error
pip install git+https://github.com/theverygaming/silly.git@6fe468a20bca129b7f92c48ac19283acb297a5b2 || goto :error
pip install requests

:loop
python main.py >> autoreload.log 2>&1
goto loop

:error
echo error!
pause
