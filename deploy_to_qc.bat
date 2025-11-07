@echo off
REM Windows wrapper to build quantconnect package using Python
SETLOCAL

python -m tools.deploy_to_qc
IF %ERRORLEVEL% NEQ 0 (
    echo Build failed with exit code %ERRORLEVEL%
    EXIT /B %ERRORLEVEL%
)

echo Build completed successfully.
ENDLOCAL
