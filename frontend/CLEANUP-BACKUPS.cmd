@echo off
cd /d E:\farmlink-production
for /R frontend %%F in (*.encoding-cleanup-*.bak) do del "%%F"
del /Q RUN-ENCODING-CLEANUP.cmd 2>nul
del /Q cleanup-frontend-encoding.py 2>nul
git status
pause
