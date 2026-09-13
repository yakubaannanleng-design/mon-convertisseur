# mon-convertisseur
Plateforme de conversion d'un document
# 🔄 Mon Convertisseur PDF

Convertisseur de fichiers **gratuit et personnel** — tes fichiers restent chez toi !

## ✨ Fonctionnalités

- 📄 PDF → Word
- 📝 Word → PDF (.docx, .doc, .odt, .rtf)
- 🖼️ Images → PDF (JPG, PNG, WebP, BMP)

## 🚀 Installation

```bash
# 1. Cloner le projet
git clone https://github.com/TON-PSEUDO/mon-convertisseur.git
cd mon-convertisseur

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Installer LibreOffice (pour Word → PDF)
# Linux :
sudo apt install libreoffice
# Windows : télécharger sur https://libreoffice.org

# 4. Lancer
uvicorn main:app --host 0.0.0.0 --port 8000
