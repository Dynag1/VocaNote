echo.
echo ========================================
echo   VocaNote - Build Complet (Exe + Setup)
echo ========================================
echo.

REM Vérifier si Python est installé
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installe ou n'est pas dans le PATH
    pause
    exit /b 1
)

echo [OK] Python est installe
echo.

REM Lancer le script de build unifié
echo Lancement du script de build Python...
echo Ce script va creer l'executable puis l'installateur.
echo.
python build.py

if errorlevel 1 (
    echo.
    echo [ERREUR] Le processus de build a rencontre une erreur.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Processus termine !
echo ========================================
echo.
pause
