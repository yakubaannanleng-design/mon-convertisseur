"""
Mon Convertisseur PDF — Usage personnel
Lancer avec :  uvicorn main:app --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pdf2docx import Converter
from PIL import Image
import os
import time
import uuid
import subprocess
import tempfile

app = FastAPI(title="Mon Convertisseur PDF")

UPLOAD_DIR = "fichiers"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Formats acceptés pour chaque conversion
FORMATS_WORD = (".docx", ".doc", ".odt", ".rtf")
FORMATS_IMAGES = (".jpg", ".jpeg", ".png", ".webp", ".bmp")


def nettoyage(max_age_secondes: int = 600):
    """Supprime les fichiers de plus de 10 minutes (usage perso, on garde simple)."""
    maintenant = time.time()
    for f in os.listdir(UPLOAD_DIR):
        chemin = os.path.join(UPLOAD_DIR, f)
        if os.path.isfile(chemin) and maintenant - os.path.getmtime(chemin) > max_age_secondes:
            try:
                os.remove(chemin)
            except OSError:
                pass


def sauvegarder_fichier(fichier: UploadFile, suffixe: str = "") -> str:
    """Sauvegarde le fichier uploadé et retourne son chemin."""
    id_unique = uuid.uuid4().hex[:10]
    extension = os.path.splitext(fichier.filename)[1].lower()
    chemin = os.path.join(UPLOAD_DIR, f"{id_unique}{suffixe}{extension}")
    with open(chemin, "wb") as f:
        f.write(fichier.file.read())
    return chemin


def verifier_extension(fichier: UploadFile, extensions: tuple):
    extension = os.path.splitext(fichier.filename)[1].lower()
    if extension not in extensions:
        raise HTTPException(
            400,
            f"Format non supporté : '{extension}'. Formats acceptés : {', '.join(extensions)}"
        )


# ==================== PDF → WORD ====================

@app.post("/api/pdf-vers-word")
async def pdf_vers_word(fichier: UploadFile = File(...)):
    verifier_extension(fichier, (".pdf",))
    nettoyage()

    chemin_pdf = sauvegarder_fichier(fichier)
    chemin_docx = os.path.splitext(chemin_pdf)[0] + ".docx"

    try:
        cv = Converter(chemin_pdf)
        cv.convert(chemin_docx)
        cv.close()
    except Exception as e:
        if os.path.exists(chemin_pdf):
            os.remove(chemin_pdf)
        raise HTTPException(500, f"Erreur lors de la conversion : {e}")

    os.remove(chemin_pdf)
    nom_sortie = os.path.splitext(fichier.filename)[0] + ".docx"

    return FileResponse(
        chemin_docx,
        filename=nom_sortie,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


# ==================== WORD → PDF ====================

@app.post("/api/word-vers-pdf")
async def word_vers_pdf(fichier: UploadFile = File(...)):
    verifier_extension(fichier, FORMATS_WORD)
    nettoyage()

    chemin_docx = sauvegarder_fichier(fichier)
    chemin_pdf = os.path.splitext(chemin_docx)[0] + ".pdf"

    try:
        resultat = subprocess.run(
            ["libreoffice", "--headless", "--convert-to", "pdf",
             "--outdir", UPLOAD_DIR, chemin_docx],
            capture_output=True, timeout=120
        )
        if not os.path.exists(chemin_pdf):
            raise RuntimeError(resultat.stderr.decode()[:300] or "LibreOffice a échoué")
    except FileNotFoundError:
        if os.path.exists(chemin_docx):
            os.remove(chemin_docx)
        raise HTTPException(
            500,
            "LibreOffice n'est pas installé. Installe-le avec : sudo apt install libreoffice"
        )
    except Exception as e:
        if os.path.exists(chemin_docx):
            os.remove(chemin_docx)
        raise HTTPException(500, f"Erreur lors de la conversion : {e}")

    os.remove(chemin_docx)
    nom_sortie = os.path.splitext(fichier.filename)[0] + ".pdf"

    return FileResponse(chemin_pdf, filename=nom_sortie, media_type="application/pdf")


# ==================== IMAGES → PDF ====================

@app.post("/api/images-vers-pdf")
async def images_vers_pdf(fichiers: list[UploadFile] = File(...)):
    nettoyage()
    images = []
    fichiers_temp = []

    try:
        for fichier in sorted(fichiers, key=lambda f: f.filename):
            verifier_extension(fichier, FORMATS_IMAGES)
            chemin = sauvegarder_fichier(fichier)
            fichiers_temp.append(chemin)
            images.append(Image.open(chemin).convert("RGB"))
    except HTTPException:
        for chemin in fichiers_temp:
            if os.path.exists(chemin):
                os.remove(chemin)
        raise

    if not images:
        raise HTTPException(400, "Aucune image reçue !")

    chemin_pdf = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex[:10]}.pdf")

    if len(images) == 1:
        images[0].save(chemin_pdf, "PDF", resolution=150.0)
    else:
        images[0].save(chemin_pdf, "PDF", save_all=True,
                       append_images=images[1:], resolution=150.0)

    for chemin in fichiers_temp:
        os.remove(chemin)

    return FileResponse(chemin_pdf, filename="images_converties.pdf",
                        media_type="application/pdf")


# ==================== PAGE D'ACCUEIL ====================

@app.get("/", response_class=HTMLResponse)
async def accueil():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()
