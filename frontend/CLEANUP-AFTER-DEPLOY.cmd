@echo off
cd /d E:\farmlink-production
for /R frontend %%F in (*.global-corruption-fix-*.bak) do del "%%F"
del /Q RUN-GLOBAL-FIX.cmd 2>nul
del /Q fix-global-corruption.py 2>nul
git restore README.txt 2>nul
git status
pause
