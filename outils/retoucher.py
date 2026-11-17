"""Retouche « style GBIC » d'un détourage WebP RGBA (personnes du site).

Reproduit le style des deux retouches faites à la main (ingenieure, acheteur) :
  1. courbe de tons sur la luminance : ombres un peu plus denses, tons moyens et
     hautes lumières nettement relevés (contraste global plus fort) ;
  2. netteté fine (petit rayon) avec seuil anti-bruit ;
  3. clarté (micro-contraste à rayon moyen) ;
  4. saturation plus dense sur les couleurs déjà franches, gris et noirs protégés ;
  5. compression douce des couleurs qui sortiraient de la gamme (pas d'aplat cramé).
L'alpha n'est jamais modifié. Les zones transparentes n'influencent pas les flous
(flous normalisés par l'alpha), donc pas de halo sombre sur le contour.

Usage :
    python outils/retoucher.py <entrée.webp> <sortie.webp> [--cote-ref 1000] [--qualite 90]

--cote-ref : côté long (px) auquel l'image sera affichée sur le site. Les rayons
ci-dessous sont donnés pour ce côté et agrandis si la source est plus grande.
Dépendances : Pillow et numpy uniquement.
"""
import argparse
import sys

import numpy as np
from PIL import Image

# ---------------------------------------------------------------------------
# Paramètres réglables
# ---------------------------------------------------------------------------

# Courbe de tons (entrée, sortie), 0-255, interpolée en douceur. Mesurée sur les deux
# retouches : ombres un peu plus denses (32 -> 27), 80 inchangé, tons moyens et hautes
# lumières nettement relevés (128 -> 156, 192 -> 227), blanc juste sous 255.
COURBE = [
    (0, 2), (16, 9), (32, 27), (48, 43), (64, 61), (80, 79), (96, 101),
    (112, 128), (128, 156), (144, 179), (160, 198), (176, 214), (192, 227),
    (208, 238), (224, 246), (240, 251), (255, 253),
]
# Dosage global de la courbe (0 = aucune, 1 = courbe telle quelle).
COURBE_FORCE = 1.0
# Couleurs vives (gilet orange, casque rouge) : la courbe est lue sur un mélange
# luminance / canal le plus fort. 0 = luminance seule (les couleurs saturées sont
# éclaircies comme des gris et se délavent), 1 = canal le plus fort (elles bougent peu).
VIVES_LUMIERE = 0.65

# Netteté fine : détail = L - flou(L, rayon), ajouté avec ce gain.
NETTETE_GAIN = 1.4
NETTETE_RAYON = 1.0      # px, pour une image au côté de référence
NETTETE_SEUIL = 1.5      # en niveaux : les écarts plus petits (grain) sont épargnés

# Clarté : flou(L, petit) - flou(L, grand), ajouté avec ce gain.
CLARTE_GAIN = 0.225
CLARTE_RAYON_PETIT = 3.0
CLARTE_RAYON_GRAND = 24.0
# Plafond doux du détail ajouté (niveaux) : limite les halos sur les bords très contrastés.
DETAIL_MAX = 40.0

# Couleur : la chroma (écart de chaque canal à la luminance) est multipliée par
#   (1 + (SATURATION - 1) * protection(chroma)) * (L_sortie / L_entrée) ** SUIVI_LUMIERE
SATURATION = 1.35
CHROMA_PROTEGEE = 10.0   # en dessous : gris quasi neutres, pas de gain
CHROMA_PLEINE = 50.0     # au-dessus : gain complet
SUIVI_LUMIERE = 0.30     # la couleur suit un peu l'éclaircissement (0 = pas du tout)
# Couleurs qui sortent de la gamme (orange fluo très éclairci) : 0 = on garde la lumière
# et on désature (couleur délavée), 1 = on garde la saturation et on assombrit un peu.
GAMME_GARDE_SATURATION = 0.0

# Côté long d'affichage par défaut (le site publie les personnes à 1000 px).
COTE_REF = 1000
QUALITE = 90

# Coefficients de luminance (Rec. 709 / sRGB)
KR, KG, KB = 0.2126, 0.7152, 0.0722


# ---------------------------------------------------------------------------
# Outils
# ---------------------------------------------------------------------------

def _boite(x, r, axe):
    """Flou boîte de rayon entier r le long d'un axe, bords répliqués."""
    if r < 1:
        return x
    pad = [(0, 0)] * x.ndim
    pad[axe] = (r + 1, r)
    c = np.cumsum(np.pad(x, pad, mode="edge"), axis=axe, dtype=np.float64)
    n = x.shape[axe]
    haut = np.take(c, np.arange(2 * r + 1, 2 * r + 1 + n), axis=axe)
    bas = np.take(c, np.arange(0, n), axis=axe)
    return (haut - bas) / (2 * r + 1)


def flou_gaussien(x, sigma):
    """Flou gaussien approché (3 passes de flou boîte ; noyau 3x3 pour sigma < ~1.2)."""
    if sigma <= 0:
        return x
    largeur = np.sqrt(12.0 * sigma * sigma / 3.0 + 1.0)
    r = int(round((largeur - 1.0) / 2.0))
    if r < 1:
        k = np.exp(-np.array([1.0, 0.0, 1.0]) / (2.0 * sigma * sigma))
        k /= k.sum()
        for axe in (0, 1):
            p = [(0, 0)] * x.ndim
            p[axe] = (1, 1)
            xp = np.pad(x, p, mode="edge")
            n = x.shape[axe]
            x = (k[0] * np.take(xp, np.arange(0, n), axis=axe)
                 + k[1] * np.take(xp, np.arange(1, n + 1), axis=axe)
                 + k[2] * np.take(xp, np.arange(2, n + 2), axis=axe))
        return x
    for _ in range(3):
        x = _boite(x, r, 0)
        x = _boite(x, r, 1)
    return x


def flou_alpha(x, poids, sigma):
    """Flou normalisé par l'alpha : le fond transparent ne « bave » pas sur le sujet."""
    return flou_gaussien(x * poids, sigma) / np.maximum(flou_gaussien(poids, sigma), 1e-4)


def courbe_lisse(points):
    """Table 0..255 d'une courbe monotone (interpolation cubique de Fritsch-Carlson)."""
    xs = np.array([p[0] for p in points], dtype=float)
    ys = np.array([p[1] for p in points], dtype=float)
    h = np.diff(xs)
    d = np.diff(ys) / h
    m = np.zeros_like(xs)
    m[0], m[-1] = d[0], d[-1]
    for i in range(1, len(xs) - 1):
        if d[i - 1] * d[i] > 0:
            w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
    t = np.arange(256, dtype=float)
    i = np.clip(np.searchsorted(xs, t, side="right") - 1, 0, len(xs) - 2)
    s = (t - xs[i]) / h[i]
    h00, h10 = 2 * s ** 3 - 3 * s ** 2 + 1, s ** 3 - 2 * s ** 2 + s
    h01, h11 = -2 * s ** 3 + 3 * s ** 2, s ** 3 - s ** 2
    return h00 * ys[i] + h10 * h[i] * m[i] + h01 * ys[i + 1] + h11 * h[i] * m[i + 1]


def appliquer_table(table, v):
    """Applique une table 0..255 à des valeurs flottantes (interpolation linéaire)."""
    return np.interp(np.clip(v, 0, 255), np.arange(256), table)


# ---------------------------------------------------------------------------
# Retouche
# ---------------------------------------------------------------------------

def retoucher(rgba, cote_ref=COTE_REF):
    """rgba : tableau uint8 (H, W, 4). Renvoie un tableau uint8 de même forme, alpha intact."""
    rgb = rgba[..., :3].astype(np.float64)
    alpha = rgba[..., 3]
    poids = alpha.astype(np.float64) / 255.0
    echelle = max(1.0, max(rgba.shape[:2]) / float(cote_ref))

    lum = KR * rgb[..., 0] + KG * rgb[..., 1] + KB * rgb[..., 2]

    # 1. courbe de tons
    table = courbe_lisse(COURBE)
    clarte_percue = lum + VIVES_LUMIERE * (rgb.max(-1) - lum)
    base = lum + COURBE_FORCE * (appliquer_table(table, clarte_percue) - clarte_percue)

    # 2. netteté fine, avec seuil anti-grain
    fin = lum - flou_alpha(lum, poids, NETTETE_RAYON * echelle)
    fin *= 1.0 - np.exp(-(fin / max(NETTETE_SEUIL, 1e-3)) ** 2)

    # 3. clarté (micro-contraste)
    moyen = (flou_alpha(lum, poids, CLARTE_RAYON_PETIT * echelle)
             - flou_alpha(lum, poids, CLARTE_RAYON_GRAND * echelle))

    detail = NETTETE_GAIN * fin + CLARTE_GAIN * moyen
    detail = DETAIL_MAX * np.tanh(detail / DETAIL_MAX)
    lum_sortie = np.clip(base + detail, 0, 255)

    # 4. couleur : chroma renforcée sur les couleurs franches, gris protégés
    chroma = rgb - lum[..., None]
    norme = np.sqrt((chroma ** 2).sum(-1))
    protection = np.clip((norme - CHROMA_PROTEGEE) / max(CHROMA_PLEINE - CHROMA_PROTEGEE, 1e-3), 0, 1)
    protection = protection * protection * (3 - 2 * protection)  # transition douce
    gain = 1.0 + (SATURATION - 1.0) * protection
    rapport = np.clip((lum_sortie + 2.0) / (lum + 2.0), 0.0, 2.0)
    gain = gain * rapport ** SUIVI_LUMIERE
    chroma = chroma * gain[..., None]

    # 5. compression de gamme : deux façons de ramener dans 0..255 une couleur qui déborde,
    #    mélangées par GAMME_GARDE_SATURATION :
    #    a) réduire la chroma en gardant la luminance (couleur plus pâle) ;
    #    b) réduire l'ensemble en gardant les proportions R:G:B (couleur un peu plus sombre).
    haut = chroma.max(-1)
    bas = chroma.min(-1)
    k = np.ones_like(lum_sortie)
    depasse_haut = lum_sortie + haut > 255
    k[depasse_haut] = (255 - lum_sortie[depasse_haut]) / np.maximum(haut[depasse_haut], 1e-6)
    depasse_bas = lum_sortie + bas < 0
    k[depasse_bas] = np.minimum(k[depasse_bas], lum_sortie[depasse_bas] / np.maximum(-bas[depasse_bas], 1e-6))
    pale = lum_sortie[..., None] + chroma * np.clip(k, 0, 1)[..., None]
    brut = np.maximum(lum_sortie[..., None] + chroma, 0)
    sombre = brut * np.minimum(1.0, 255.0 / np.maximum(brut.max(-1), 1e-6))[..., None]
    sortie = (1 - GAMME_GARDE_SATURATION) * pale + GAMME_GARDE_SATURATION * sombre

    resultat = np.empty_like(rgba)
    resultat[..., :3] = np.clip(np.round(sortie), 0, 255).astype(np.uint8)
    resultat[..., 3] = alpha
    return resultat


def main(argv=None):
    p = argparse.ArgumentParser(description="Retouche style GBIC d'un détourage WebP RGBA.")
    p.add_argument("entree")
    p.add_argument("sortie")
    p.add_argument("--cote-ref", type=int, default=COTE_REF,
                   help="côté long d'affichage sur le site (px), défaut %(default)s")
    p.add_argument("--qualite", type=int, default=QUALITE)
    a = p.parse_args(argv)

    im = Image.open(a.entree).convert("RGBA")
    out = Image.fromarray(retoucher(np.asarray(im), a.cote_ref), "RGBA")
    out.save(a.sortie, "WEBP", quality=a.qualite, method=6, exact=True)
    print(f"{a.entree} -> {a.sortie} ({im.size[0]}x{im.size[1]})")


if __name__ == "__main__":
    sys.exit(main())
