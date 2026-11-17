"""Retrouve où chaque détourage se trouve dans sa photo d'origine.

Le détourage est recadré sur le sujet ; pour le reposer exactement sur le fond reconstruit par Gemini,
il faut sa position dans la photo d'origine. On la retrouve par corrélation (OpenCV).
Sortie : outils/positions.json, en fractions de la largeur et de la hauteur de la photo d'origine.

Usage : python outils/positions_detourages.py
"""
import json
import os

import cv2
import numpy as np

ICI = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(ICI, "..", "..", "site", "images")
NOMS = {
    "ingenieure": "personne-05-ingenieure-gilet-orange",
    "mineur": "personne-08-mineur-casque",
    "chef-chantier": "personne-02-chef-chantier-route",
    "magasinier": "personne-09-magasinier-cartons",
    "cheffe-cuisine": "personne-11-cheffe-cuisine",
    "eleveur": "personne-13-eleveur-poulailler",
    "technicien": "personne-03-technicien-casque-rouge",
    "acheteur": "personne-14-acheteur-telephone",
}


def lire(chemin, drapeau=cv2.IMREAD_UNCHANGED):
    return cv2.imdecode(np.fromfile(chemin, dtype=np.uint8), drapeau)


def reduire(image, cote=2400):
    """Comme detourer.py : le côté long est ramené à 2400 px avant le détourage."""
    h, w = image.shape[:2]
    if max(h, w) <= cote:
        return image
    f = cote / max(h, w)
    return cv2.resize(image, (round(w * f), round(h * f)), interpolation=cv2.INTER_AREA)


def main():
    resultats = {}
    for nom, base in NOMS.items():
        photo = reduire(lire(os.path.join(SOURCE, "originales", base + ".jpg"), cv2.IMREAD_COLOR))
        sujet = lire(os.path.join(SOURCE, "detourees", base + ".webp"))
        # L'éleveur a été détouré depuis sa version recadrée : on cherche dans celle-ci, puis on reporte.
        decalage_x = 0
        if nom == "eleveur":
            recadree = reduire(lire(os.path.join(SOURCE, "originales", base + "-recadre.jpg"), cv2.IMREAD_COLOR))
            r = cv2.matchTemplate(photo, recadree[: recadree.shape[0] // 3, : recadree.shape[1] // 3], cv2.TM_SQDIFF)
            decalage_x = cv2.minMaxLoc(r)[2][0]
            photo_recherche = recadree
        else:
            photo_recherche = photo
        H, W = photo.shape[:2]
        h, w = sujet.shape[:2]
        facteur = 4
        petite = cv2.resize(photo_recherche, (photo_recherche.shape[1] // facteur, photo_recherche.shape[0] // facteur), interpolation=cv2.INTER_AREA)
        modele = cv2.resize(sujet[:, :, :3], (w // facteur, h // facteur), interpolation=cv2.INTER_AREA)
        masque = (cv2.resize(sujet[:, :, 3], (w // facteur, h // facteur)) > 200).astype(np.uint8) * 255
        r = cv2.matchTemplate(petite, modele, cv2.TM_SQDIFF, mask=masque)
        _, _, (x, y), _ = cv2.minMaxLoc(r)
        # Affinage à pleine résolution autour de la position trouvée.
        x, y = x * facteur, y * facteur
        x0, y0 = max(0, x - 8), max(0, y - 8)
        zone = photo_recherche[y0 : y0 + h + 16, x0 : x0 + w + 16]
        r = cv2.matchTemplate(zone, sujet[:, :, :3], cv2.TM_SQDIFF, mask=(sujet[:, :, 3] > 200).astype(np.uint8) * 255)
        _, _, (dx, dy), _ = cv2.minMaxLoc(r)
        x, y = x0 + dx + decalage_x, y0 + dy
        resultats[nom] = {"x": round(x / W, 5), "y": round(y / H, 5), "l": round(w / W, 5), "h": round(h / H, 5), "ratio": round(W / H, 5)}
        print(nom, resultats[nom])
    with open(os.path.join(ICI, "positions.json"), "w", encoding="utf-8") as f:
        json.dump(resultats, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
