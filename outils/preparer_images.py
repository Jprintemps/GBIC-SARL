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


# Chaque image existe en plusieurs largeurs, en AVIF (léger) et en WebP (repli pour les vieux navigateurs).
# Le navigateur choisit la plus petite qui suffit à l'écran : un téléphone en 2G ne charge jamais le 1 600 px.
QUALITE_AVIF = 40
QUALITE_WEBP = 62
LARGEURS = {"fonds": (480, 960, 1600), "calques": (360, 720, 1100), "scenes": (480, 960, 1400)}
MANIFESTE = os.path.join(ICI, "variantes.json")


def exporter(im, dossier, nom, manifeste):
    """Écrit nom-<largeur>.avif et .webp pour chaque largeur utile, et note les largeurs dans le manifeste."""
    cle = os.path.basename(dossier)
    largeurs = sorted({min(l, im.width) for l in LARGEURS[cle]})
    for l in largeurs:
        copie = im if l == im.width else im.resize((l, round(im.height * l / im.width)), Image.LANCZOS)
        copie.save(os.path.join(dossier, f"{nom}-{l}.avif"), "AVIF", quality=QUALITE_AVIF, speed=6)
        copie.save(os.path.join(dossier, f"{nom}-{l}.webp"), "WEBP", quality=QUALITE_WEBP, method=6)
    manifeste[f"{cle}/{nom}"] = {"largeurs": largeurs, "ratio": round(im.width / im.height, 5)}


def lire_manifeste():
    import json
    return json.load(open(MANIFESTE, encoding="utf-8")) if os.path.exists(MANIFESTE) else {}


def ecrire_manifeste(manifeste):
    import json
    with open(MANIFESTE, "w", encoding="utf-8") as f:
        json.dump(dict(sorted(manifeste.items())), f, indent=1, ensure_ascii=False)


def vider(dossier):
    os.makedirs(dossier, exist_ok=True)
    for f in os.listdir(dossier):
        os.remove(os.path.join(dossier, f))


def main():
    manifeste = {}
    vider(FONDS)
    vider(CALQUES)
    for nom, (fichier, cadre) in PHOTOS.items():
        im = Image.open(os.path.join(SOURCE, "originales", fichier)).convert("RGB")
        if cadre:
            w, h = im.size
            im = im.crop((int(cadre[0] * w), int(cadre[1] * h), int(cadre[2] * w), int(cadre[3] * h)))
        im.thumbnail((1600, 2400), Image.LANCZOS)
        exporter(im, FONDS, nom, manifeste)
    for nom, (fichier, cote) in DETOURAGES.items():
        retouche = os.path.join(RETOUCHEES, f"{nom}.webp")
        source = retouche if os.path.exists(retouche) else os.path.join(SOURCE, "detourees", fichier)
        im = Image.open(source).convert("RGBA")
        im.thumbnail((cote, cote), Image.LANCZOS)
        exporter(im, CALQUES, nom, manifeste)
    preparer_scenes(manifeste)
    ecrire_manifeste(manifeste)
    for dossier in (FONDS, CALQUES, SCENES):
        total = sum(os.path.getsize(os.path.join(dossier, f)) for f in os.listdir(dossier) if f.endswith(".avif"))
        print(f"{os.path.relpath(dossier, RACINE)} : {len(os.listdir(dossier))} fichiers, {total / 1e6:.2f} Mo en AVIF")


# Scènes où l'on garde la photo d'origine en pleine résolution et où Gemini ne remplit que la zone du sujet.
# Réservé aux images où le raccord ne se voit pas (Gemini ne recadre pas toujours au pixel près).
HYBRIDES = {"camion-laterite", "camion-piste"}


def preparer_scenes(manifeste=None):
    """Calque arrière de chaque scène : la photo d'origine en pleine résolution, sauf derrière le sujet,
    où l'on prend le décor reconstruit par Gemini (Gemini rend des images d'environ 1 200 px seulement).
    La zone empruntée à Gemini est la silhouette du sujet, élargie et adoucie pour que le raccord ne se voie pas."""
    import json
    from PIL import ImageFilter
    autonome = manifeste is None
    if autonome:
        manifeste = lire_manifeste()
    vider(SCENES)
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
            exporter(im, SCENES, nom, manifeste)
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
        im.thumbnail((1400, 1920), Image.LANCZOS)
        exporter(im, SCENES, nom, manifeste)
    if autonome:
        ecrire_manifeste(manifeste)


if __name__ == "__main__":
    import sys
    if sys.argv[1:] == ["scenes"]:
        preparer_scenes()
    else:
        main()
