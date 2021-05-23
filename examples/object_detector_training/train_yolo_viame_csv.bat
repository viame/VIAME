@echo off

REM Input locations and types
SET INPUT_DIRECTORY=training_data_mouss

REM Path to VIAME installation
SET VIAME_INSTALL=.\..\..

CALL "%VIAME_INSTALL%\setup_viame.bat"

REM Adjust log level
SET KWIVER_DEFAULT_LOG_LEVEL=info

REM Run Pipeline
viame_train_detector.exe ^
  -i "%INPUT_DIRECTORY%" ^
  -c "%VIAME_INSTALL%\configs\pipelines\train_yolo_640.viame_csv.conf" ^
  --threshold 0.0

pause

