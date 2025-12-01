import os
import shutil
import sys

print("🔍 Vérification de l'environnement VocaNote...")
print("-" * 50)

# 1. Vérifier le dossier ffmpeg local
local_ffmpeg = os.path.join(os.getcwd(), "ffmpeg", "bin")
if os.path.exists(local_ffmpeg):
    print(f"✅ Dossier FFmpeg local trouvé: {local_ffmpeg}")
    # Ajouter au PATH pour le test
    os.environ["PATH"] = local_ffmpeg + os.pathsep + os.environ["PATH"]
else:
    print("❌ Dossier FFmpeg local NON trouvé")
    print("   👉 Veuillez exécuter 'installer_ffmpeg.bat'")

# 2. Vérifier la commande ffmpeg
ffmpeg_path = shutil.which("ffmpeg")
if ffmpeg_path:
    print(f"✅ Commande ffmpeg trouvée: {ffmpeg_path}")
else:
    print("❌ Commande ffmpeg NON trouvée dans le PATH")

# 3. Vérifier les modules Python
try:
    import whisper
    print("✅ Module whisper installé")
except ImportError:
    print("❌ Module whisper NON installé")

try:
    import PyQt6
    print("✅ Module PyQt6 installé")
except ImportError:
    print("❌ Module PyQt6 NON installé")

print("-" * 50)
if ffmpeg_path:
    print("🎉 Tout semble prêt ! Vous pouvez lancer main.py")
else:
    print("⚠️ Il manque FFmpeg. La transcription ne fonctionnera pas.")
