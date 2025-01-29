@echo off
if not exist autoreload_venv python -m venv autoreload_venv || goto :error
call autoreload_venv\Scripts\activate.bat || goto :error
pip install git+https://github.com/theverygaming/silly.git@5d852ced63775656afb4ba878d04021c42149d06 || goto :error
pip install requests

:loop
python main.py >> autoreload.log 2>&1
goto loop

:error
echo error!
pause
