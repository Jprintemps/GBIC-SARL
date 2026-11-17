"""Prépare les images du site à partir de ../site/images (originales et détourées).

Usage : python outils/preparer_images.py
Sortie : assets/img/fonds (photos de fond, 1920 et 960 px) et assets/img/calques (détourages WebP).
"""
import os
from PIL import Image

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
SOURCE = os.path.join(RACINE, "..", "site", "images")
FONDS = os.path.join(RACINE, "assets", "img", "fonds")
CALQUES = os.path.join(RACINE, "assets", "img", "calques")
# Retouches faites à la main : si <nom>.webp existe ici, il remplace le détourage automatique.
RETOUCHEES = os.path.join(SOURCE, "retouchees")

# nom publié : (fichier source, recadrage optionnel en fractions gauche, haut, droite, bas)
PHOTOS = {
    "mine-terrasses": ("decor-01-mine-terrasses.jpg", None),
    "mine-tombereau": ("decor-02-mine-tombereau.jpg", None),
    "mine-aerienne": ("decor-03-mine-aerienne.jpg", None),
    "camions-piste": ("decor-05-camions-piste.jpg", None),
    "camion-piste-ocre": ("decor-06-camion-piste-orange.jpg", None),
    "concassage": ("decor-07-concassage.jpg", None),
    "rouleaux-papier": ("decor-08-rouleaux-papier.jpg", (0, 0.2, 1, 0.75)),
    "eleveuse-poules": ("decor-09-eleveuse-poules.jpg", None),
    "flotte-camions": ("camion-04-flotte-rouge.jpg", (0, 0.3, 1, 0.75)),
}

# nom publié : (fichier détouré, côté long maximal)
DETOURAGES = {
    "ingenieure": ("personne-05-ingenieure-gilet-orange.webp", 1300),
    "mineur": ("personne-08-mineur-casque.webp", 1000),
    "chef-chantier": ("personne-02-chef-chantier-route.webp", 1000),
    "magasinier": ("personne-09-magasinier-cartons.webp", 1000),
    "cheffe-cuisine": ("personne-11-cheffe-cuisine.webp", 1000),
    "eleveur": ("personne-13-eleveur-poulailler.webp", 1000),
    "technicien": ("personne-03-technicien-casque-rouge.webp", 1000),
    "acheteur": ("personne-14-acheteur-telephone.webp", 1000),
    "howo-profil": ("camion-ia-02-howo-profil-chatgpt.webp", 1200),
    "howo-trois-quarts": ("camion-ia-01-howo-trois-quarts-chatgpt.webp", 1200),
    "malachite": ("mineral-01-malachite-chatgpt.webp", 640),
    "heterogenite": ("mineral-02-heterogenite-chatgpt.webp", 640),
    "cuivre-natif": ("mineral-03-cuivre-natif-chatgpt.webp", 640),
    "chalcopyrite": ("mineral-05-chalcopyrite-chatgpt.webp", 640),
    "cobalt": ("mineral-06-cobalt-metal-chatgpt.webp", 640),
    "cathodes": ("mineral-07-cathodes-cuivre-chatgpt.webp", 900),
}


def main():
    os.makedirs(FONDS, exist_ok=True)
    os.makedirs(CALQUES, exist_ok=True)
    for nom, (fichier, cadre) in PHOTOS.items():
        im = Image.open(os.path.join(SOURCE, "originales", fichier)).convert("RGB")
        if cadre:
            w, h = im.size
            im = im.crop((int(cadre[0] * w), int(cadre[1] * h), int(cadre[2] * w), int(cadre[3] * h)))
        for largeur in (1920, 960):
            copie = im.copy()
            if copie.width > largeur:
                copie = copie.resize((largeur, round(copie.height * largeur / copie.width)), Image.LANCZOS)
            copie.save(os.path.join(FONDS, f"{nom}-{largeur}.webp"), "WEBP", quality=70, method=6)
    for nom, (fichier, cote) in DETOURAGES.items():
        retouche = os.path.join(RETOUCHEES, f"{nom}.webp")
        source = retouche if os.path.exists(retouche) else os.path.join(SOURCE, "detourees", fichier)
        im = Image.open(source).convert("RGBA")
        im.thumbnail((cote, cote), Image.LANCZOS)
        im.save(os.path.join(CALQUES, f"{nom}.webp"), "WEBP", quality=80, method=6)
    for dossier in (FONDS, CALQUES):
        total = sum(os.path.getsize(os.path.join(dossier, f)) for f in os.listdir(dossier))
        print(f"{os.path.relpath(dossier, RACINE)} : {len(os.listdir(dossier))} fichiers, {total / 1e6:.1f} Mo")


if __name__ == "__main__":
    main()
