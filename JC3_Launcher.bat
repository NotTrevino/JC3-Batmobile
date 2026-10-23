@echo off
title JC3 Launcher

cd /d "D:\Games\Just Cause 3"

start "" "JustCause3.exe" --vfs-fs dropzone --vfs-archive patch_win64 --vfs-archive archives_win64 --vfs-archive dlc_win64 --vfs-fs .

exit