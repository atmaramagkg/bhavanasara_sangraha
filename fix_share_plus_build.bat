@echo off
setlocal enabledelayedexpansion

REM ============================================================
REM  fix_share_plus_build.bat
REM
REM  Fixes: "cannot find symbol SharePlusPlugin" in
REM  GeneratedPluginRegistrant.java.
REM
REM  This script ONLY touches build outputs, caches, and the
REM  auto-regenerated pubspec.lock file. It never touches your
REM  lib/, android/app/src, assets/, or any source you've written.
REM
REM  Run this from your project root, i.e. the same folder that
REM  contains pubspec.yaml (C:\Users\austr\bhavanasara_sangraha).
REM ============================================================

echo.
echo === Step 0: sanity check ===
if not exist "pubspec.yaml" (
    echo ERROR: pubspec.yaml not found in this folder.
    echo Please copy this script into your project root
    echo ^(the same folder as pubspec.yaml^) and run it from there.
    pause
    exit /b 1
)
echo OK - found pubspec.yaml, continuing.

echo.
echo === Step 1: flutter clean ===
call flutter clean
if errorlevel 1 (
    echo WARNING: flutter clean reported an error. Continuing anyway.
)

echo.
echo === Step 2: remove pubspec.lock (safe - auto-regenerated) ===
if exist "pubspec.lock" (
    del /f /q "pubspec.lock"
    echo Removed pubspec.lock.
) else (
    echo pubspec.lock not found, skipping.
)

echo.
echo === Step 3: clear cached share_plus Gradle artifact ===
set "SHAREPLUS_CACHE=%USERPROFILE%\.gradle\caches\modules-2\files-2.1\dev.fluttercommunity.plus.share"
if exist "%SHAREPLUS_CACHE%" (
    rmdir /s /q "%SHAREPLUS_CACHE%"
    echo Removed cached share_plus artifact:
    echo   %SHAREPLUS_CACHE%
) else (
    echo No cached share_plus artifact found at that path, skipping.
    echo ^(This is fine - it just means Gradle will fetch fresh anyway.^)
)

echo.
echo === Step 4: gradlew clean ===
if exist "android\gradlew.bat" (
    pushd android
    call gradlew.bat clean
    popd
) else (
    echo android\gradlew.bat not found, skipping this step.
)

echo.
echo === Step 5: flutter pub get ===
call flutter pub get
if errorlevel 1 (
    echo ERROR: flutter pub get failed. Fix any errors shown above before rebuilding.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  Done. Caches cleared and dependencies re-resolved fresh.
echo  Now run your normal build command, e.g.:
echo.
echo      flutter run
echo.
echo  GeneratedPluginRegistrant.java will be regenerated on this
echo  next build against whatever share_plus version actually
echo  gets resolved, so it should match reality this time.
echo ============================================================
echo.
pause
