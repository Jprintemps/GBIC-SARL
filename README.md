# GBIC-SARL

Site vitrine de **Global Business Investments Congo** (Lubumbashi), en HTML, CSS et JavaScript pur, sans dépendance. Le parallaxe est fait main dans `assets/js/main.js`.

## Pages

| Fichier | Page |
|---|---|
| `index.html` | Accueil, en parallaxe |
| `metiers/index.html` | Nos métiers |
| `metiers/*.html` | Les 6 pages métiers |
| `a-propos.html` | À propos et mot du fondateur |
| `securite.html` | Sécurité (HSE) |
| `devis.html` | Formulaire de devis |

## Modifier le site

Les pages sont générées : on ne modifie pas les `.html` de la racine à la main.

- Textes de l'accueil, de l'À propos, de la Sécurité, du devis et de Nos métiers : `src/*.html`.
- Pages métiers, numéro WhatsApp, adresse d'envoi du formulaire, blocs conditionnels : en haut de `outils/construire.py`.
- Puis on reconstruit :

```
python outils/construire.py
```

Les images viennent de `../site/images` (originales et détourées). Pour les régénérer :

```
python outils/preparer_images.py
```

Pour voir le site en local : `python -m http.server 8765`, puis http://localhost:8765.

## Le parallaxe

Dans le HTML, on pose des attributs ; le script fait le reste.

- `data-scene` : la section qui sert de repère.
- `data-vitesse="0.3"` : le calque monte plus vite que la page (premier plan). Une valeur négative le ralentit (arrière-plan).
- `data-rotation="40"` : il tourne de 40° pendant la traversée. `data-x` le déplace en largeur.
- `data-route` : il traverse sa scène de gauche à droite (le camion de « Comment ça se passe »).
- `data-habitude` : la carte du corridor se dessine pendant le défilement.
- `data-revele` : apparition douce à l'entrée dans l'écran.

Tout mouvement s'arrête si le visiteur a demandé moins d'animations dans son système.

## Avant la mise en ligne

Les repères `[entre crochets]` en police à chasse fixe sont des informations que GBIC doit fournir (voir la section 10 de `../site/copywriting-site-gbic.md`). On ne publie pas tant qu'il en reste.

1. Dans `outils/construire.py` : `WHATSAPP` (numéro), `FORMULAIRE_ENVOI` (service qui reçoit le formulaire, par exemple Formspree). Sans adresse d'envoi, le formulaire affiche son message d'erreur et renvoie vers WhatsApp : il ne fait jamais semblant d'avoir envoyé.
2. `BLOCS_AFFICHES` : retirer `"arsp"` si GBIC ne confirme pas le capital congolais et le numéro ARSP, et retirer `"chiffres"` si la bande de chiffres n'a pas au moins deux chiffres vrais.
3. Le dossier fournisseur (PDF) : remplacer les liens `data-dossier`.
4. Les photos Pexels illustrent des métiers : ces personnes ne doivent pas être présentées comme l'équipe ou les clients de GBIC. À remplacer par les vraies photos dès qu'elles existent.
5. Version anglaise : les textes sont prêts dans `../site/copywriting-site-gbic-en.md`, les pages restent à générer.
