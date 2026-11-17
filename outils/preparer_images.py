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
SCENES = os.path.join(RACINE, "assets", "img", "scenes")

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
    "camion-laterite": ("camion-05-benne-blanche-laterite.webp", 1200),
    "camion-piste": ("camion-01-benne-rouge-piste.webp", 1200),
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
    preparer_scenes()
    for dossier in (FONDS, CALQUES, SCENES):
        total = sum(os.path.getsize(os.path.join(dossier, f)) for f in os.listdir(dossier))
        print(f"{os.path.relpath(dossier, RACINE)} : {len(os.listdir(dossier))} fichiers, {total / 1e6:.1f} Mo")


# Scènes où l'on garde la photo d'origine en pleine résolution et où Gemini ne remplit que la zone du sujet.
# Réservé aux images où le raccord ne se voit pas (Gemini ne recadre pas toujours au pixel près).
HYBRIDES = {"camion-laterite", "camion-piste"}


def preparer_scenes():
    """Calque arrière de chaque scène : la photo d'origine en pleine résolution, sauf derrière le sujet,
    où l'on prend le décor reconstruit par Gemini (Gemini rend des images d'environ 1 200 px seulement).
    La zone empruntée à Gemini est la silhouette du sujet, élargie et adoucie pour que le raccord ne se voie pas."""
    import json
    from PIL import ImageFilter
    os.makedirs(SCENES, exist_ok=True)
    positions = json.load(open(os.path.join(ICI, "positions.json"), encoding="utf-8"))
    for nom, (fichier, _) in DETOURAGES.items():
        base = fichier[:-len(".webp")]
        gemini = os.path.join(SOURCE, "originales", "fonds-gemini", base + "-fond.jpg")
        if not os.path.exists(gemini) or nom not in positions:
            continue
        if nom not in HYBRIDES:
            # Fond 100 % Gemini : propre, mais limité à environ 1 200 px.
            im = Image.open(gemini).convert("RGB")
            im.thumbnail((1400, 1400), Image.LANCZOS)
            im.save(os.path.join(SCENES, f"{nom}.webp"), "WEBP", quality=78, method=6)
            print("scène", nom, im.size)
            continue
        photo = Image.open(os.path.join(SOURCE, "originales", base + ".jpg")).convert("RGB")
        photo.thumbnail((2400, 2400), Image.LANCZOS)
        W, H = photo.size
        fond = Image.open(gemini).convert("RGB").resize((W, H), Image.LANCZOS)
        p = positions[nom]
        sujet = Image.open(os.path.join(SOURCE, "detourees", fichier)).getchannel("A")
        sujet = sujet.resize((max(1, round(p["l"] * W)), max(1, round(p["h"] * H))), Image.LANCZOS)
        masque = Image.new("L", (W, H), 0)
        masque.paste(sujet, (round(p["x"] * W), round(p["y"] * H)))
        import cv2
        import numpy as np

        def elargir(m, rayon):
            noyau = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * rayon + 1, 2 * rayon + 1))
            return cv2.dilate(m, noyau)

        m = (np.asarray(masque) > 20).astype(np.uint8) * 255
        m = elargir(m, int(max(W, H) * 0.006))
        # Gemini ne rend pas exactement les mêmes teintes : on cale ses couleurs sur la photo,
        # en comparant un anneau autour du sujet (là où les deux images montrent le même décor).
        anneau = (elargir(m, int(max(W, H) * 0.03)) > 0) & (m == 0)
        g = np.asarray(fond, dtype=np.float32).copy()
        ph = np.asarray(photo, dtype=np.float32)
        if anneau.sum() > 500:
            for c in range(3):
                mg, sg = g[..., c][anneau].mean(), g[..., c][anneau].std() + 1e-3
                mp, sp = ph[..., c][anneau].mean(), ph[..., c][anneau].std() + 1e-3
                g[..., c] = (g[..., c] - mg) * (sp / sg) + mp
            fond = Image.fromarray(np.clip(g, 0, 255).astype(np.uint8))
        flou = int(max(W, H) * 0.016) | 1
        masque = Image.fromarray(cv2.GaussianBlur(m, (0, 0), flou / 2))
        im = Image.composite(fond, photo, masque)
        im.thumbnail((1920, 1920), Image.LANCZOS)
        im.save(os.path.join(SCENES, f"{nom}.webp"), "WEBP", quality=78, method=6)
        print("scène", nom, im.size)


if __name__ == "__main__":
    import sys
    if sys.argv[1:] == ["scenes"]:
        preparer_scenes()
    else:
        main()
