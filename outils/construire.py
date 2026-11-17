"""Construit le site statique GBIC à partir de src/ et des données ci-dessous.

Usage : python outils/construire.py
Écrit index.html, a-propos.html, securite.html, devis.html et metiers/*.html à la racine du dépôt.

Les textes viennent de ../site/copywriting-site-gbic.md (version 2).
- {{texte}} devient un repère « à remplir » visible : GBIC doit fournir l'information avant la mise en ligne.
- <!--si:nom--> … <!--/si:nom--> : bloc conditionnel, gardé seulement si « nom » est dans BLOCS_AFFICHES.
"""
import html
import os
import re

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
SRC = os.path.join(RACINE, "src")

# ---------- Réglages à compléter avec GBIC ----------
WHATSAPP = ""  # numéro au format international sans + ni espaces, ex. 243970000000
FORMULAIRE_ENVOI = ""  # adresse du service qui reçoit le formulaire (Formspree, Getform, script maison…)
# Blocs qui dépendent d'une preuve (section 9 du copywriting). Retirer un nom pour publier la version de repli.
BLOCS_AFFICHES = {"arsp", "chiffres"}

MESSAGE_WHATSAPP = "Bonjour, je voudrais un devis pour : "

METIERS = [
    {
        "slug": "services-miniers",
        "nom": "Services miniers",
        "famille": 1,
        "carte": "Exploitation sous contrat, découverture, forage et tir, réhabilitation selon les règles du Code minier.",
        "photo": "mine-tombereau",
        "personne": "mineur",
        "h1": "Vous fixez l'objectif de production, nous faisons sortir le minerai.",
        "chapo": "GBIC exploite sous contrat, du décapage à la réhabilitation, et fournit les intrants et les équipements dont vos usines de traitement ont besoin, en RDC et dans la région.",
        "titre_liste": "Ce que nous faisons",
        "liste": [
            "<strong>Exploitation sous contrat</strong> : découverture (enlèvement des stériles), extraction du minerai, respect des volumes et du budget de production fixés.",
            "<strong>Forage et tir</strong>.",
            "<strong>Services électriques et mécaniques</strong> sur site.",
            "<strong>Traitement et enrichissement des minerais</strong>.",
            "<strong>Réhabilitation des sites</strong> selon le plan environnemental approuvé {{PAR / EIES du Code minier, à vérifier}}.",
            "<strong>Fourniture d'intrants pour vos usines de traitement</strong> : {{liste réelle à confirmer : acide sulfurique, soufre, chaux, magnésie, métabisulfite…}}.",
            "<strong>Fourniture d'équipements lourds</strong> pour la mine et l'industrie.",
        ],
        "pour_qui": "Sociétés minières, usines de traitement, sous-traitants de rang 1 qui cherchent un partenaire congolais.",
        "pourquoi": "{{nombre}} engins en propre, {{nombre}} chantiers menés depuis {{année}}, {{références}}.<!--si:arsp--> Et une entreprise à capitaux congolais enregistrée à l'ARSP sous le n° {{numéro}}, ce qui peut compter dans vos obligations de sous-traitance.<!--/si:arsp-->",
        "avec": [
            ("genie-civil-materiaux", "Pistes, plateformes et bâtiments de votre base-vie."),
            ("restauration-base-vie", "Les repas de vos équipes sur le site."),
            ("logistique", "Le stockage de vos intrants et de vos pièces à Lubumbashi."),
        ],
        "bouton": "Demander un devis pour un chantier minier",
        "seo": ("Sous-traitance minière en RDC · GBIC Lubumbashi", "Découverture, extraction, forage et tir, traitement et réhabilitation. Sous-traitant minier congolais basé à Lubumbashi."),
    },
    {
        "slug": "genie-civil-materiaux",
        "nom": "Génie civil et matériaux",
        "famille": 1,
        "carte": "Sable, agrégats, ciment, briques, pavés, et démolition pour libérer vos terrains.",
        "photo": "concassage",
        "personne": "chef-chantier",
        "h1": "Les matériaux de votre chantier, livrés quand vous en avez besoin.",
        "chapo": "Sable, agrégats, ciment, briques et pavés : GBIC fournit le gros œuvre de vos constructions, et démolit ce qui doit l'être pour libérer vos terrains.",
        "titre_liste": "Ce que nous fournissons",
        "liste": [
            "<strong>Sable et agrégats</strong> (granulométrie {{à préciser}})",
            "<strong>Ciment</strong>",
            "<strong>Briques</strong>, petit et grand format",
            "<strong>Pavés et dalles</strong> pour parkings et voiries",
            "<strong>Démolition</strong> et dégagement de terrain",
        ],
        "pour_qui": "Entreprises de construction, promoteurs, sociétés minières qui construisent leurs bases-vie, particuliers qui bâtissent en volume.",
        "pourquoi": "{{carrière ou dépôt en propre ?}}, {{flotte de camions}}, livraison à Lubumbashi, Likasi et Kolwezi {{à confirmer}}.",
        "avec": [
            ("logistique", "Un stock tampon de matériaux près de votre chantier."),
            ("restauration-base-vie", "Les repas de vos équipes pendant les travaux."),
            ("produits-hygiene", "L'équipement des sanitaires une fois le bâtiment livré."),
        ],
        "bouton": "Demander un devis matériaux",
        "seo": ("Sable, ciment, briques à Lubumbashi · GBIC", "Sable, agrégats, ciment, briques et pavés livrés sur vos chantiers au Katanga. Démolition et dégagement de terrain."),
    },
    {
        "slug": "logistique",
        "nom": "Logistique, import et export",
        "famille": 1,
        "carte": "Stockage, préparation et livraison de vos marchandises, avec preuve de livraison et état des stocks.",
        "photo": "flotte-camions",
        "personne": "magasinier",
        "h1": "Vos marchandises stockées, suivies et livrées, sans que vous ayez à y penser.",
        "chapo": "GBIC reçoit vos produits, les garde dans des entrepôts propres et sécurisés, et les livre à vos clients ou à vos sites quand vous le décidez. Vous savez à tout moment ce qui est en stock et ce qui est parti.",
        "titre_liste": "Ce que nous faisons",
        "liste": [
            "<strong>Stockage</strong> en entrepôt sécurisé à Lubumbashi ({{surface}} m²).",
            "<strong>Gestion des stocks</strong> : entrées, sorties, transferts, ajustements et dates de péremption.",
            "<strong>Préparation et livraison</strong> des commandes.",
            "<strong>Preuve de livraison</strong> et documents de transport consultables et imprimables.",
            "<strong>Rapports</strong> envoyés par e-mail : état des stocks, historique, distribution.",
            "<strong>Import et export</strong> {{dédouanement assuré par GBIC ou par un commissionnaire partenaire ?}}",
        ],
        "pour_qui": "Importateurs, distributeurs, industriels et sociétés minières qui veulent confier leur stock à un tiers.",
        "pourquoi": "Vous ne payez que l'espace et le service que vous utilisez, et la facture baisse quand votre stock baisse. {{taux de livraison à l'heure, si GBIC le mesure}}",
        "avec": [
            ("produits-hygiene", "Votre stock de consommables, livré à la demande."),
            ("agropastoral", "Vivres stockés et livrés à vos cantines."),
            ("genie-civil-materiaux", "Matériaux gardés en dépôt jusqu'au jour du chantier."),
        ],
        "bouton": "Demander un devis logistique",
        "seo": ("Entreposage et logistique à Lubumbashi · GBIC", "Stockage sécurisé, gestion des stocks, livraison avec preuve et rapports par e-mail. Import et export depuis la RDC."),
    },
    {
        "slug": "restauration-base-vie",
        "nom": "Restauration et base-vie",
        "famille": 1,
        "carte": "Repas pour vos chantiers, vos bureaux {{et vos bases-vie}}, avec une partie des produits venus de nos élevages.",
        "photo": "mine-aerienne",
        "personne": "cheffe-cuisine",
        "h1": "Des repas servis à l'heure, une cantine jamais à court.",
        "chapo": "GBIC nourrit vos équipes sur vos chantiers, dans vos bureaux {{et dans vos bases-vie}}, et assure le service de vos réceptions. Une partie de ce que nous servons vient de nos propres élevages et cultures.",
        "titre_liste": "Ce que nous faisons",
        "liste": [
            "<strong>Restauration de chantier et de bureau</strong> : repas préparés et livrés, ou cuisine sur place.",
            "<strong>Restauration de base-vie</strong> {{à confirmer}} : trois repas par jour, rotations comprises.",
            "<strong>Approvisionnement des cuisines</strong> : vivres, produits frais, produits d'hygiène et d'entretien.",
            "<strong>Réceptions et événements</strong>.",
        ],
        "pour_qui": "Sociétés minières et industrielles, entreprises de construction, bureaux, organisateurs d'événements.",
        "pourquoi": "La viande, les œufs et une partie des légumes viennent de nos élevages et de nos cultures, ce qui réduit le risque de rupture. {{couverts servis par jour, sites servis}}",
        "avec": [
            ("agropastoral", "Viande, œufs et légumes livrés en volume à votre propre cuisine."),
            ("produits-hygiene", "Papier, lingettes et produits d'entretien pour la base-vie."),
            ("logistique", "Le stockage de vos vivres secs à Lubumbashi."),
        ],
        "bouton": "Demander un devis restauration",
        "seo": ("Restauration de chantier et base-vie, Katanga · GBIC", "Repas pour vos chantiers, bureaux et bases-vie, avec des produits de nos élevages. Réceptions et événements."),
    },
    {
        "slug": "agropastoral",
        "nom": "Agropastoral",
        "famille": 2,
        "carte": "Porcs, œufs, poussins d'un jour, légumes, fruits et aliments pour bétail produits en RDC.",
        "photo": "eleveuse-poules",
        "personne": "eleveur",
        "h1": "De la viande, des œufs et des légumes produits au Congo, livrés en volume.",
        "chapo": "GBIC élève et cultive en RDC pour que les hôtels, les cantines et les distributeurs de la région n'aient plus besoin d'importer ce qui pousse ici.",
        "titre_liste": "Ce que nous produisons",
        "liste": [
            "<strong>Élevage</strong> : porcs, poules pondeuses, poussins d'un jour",
            "<strong>Œufs</strong>",
            "<strong>Aliments pour bétail</strong>",
            "<strong>Cultures</strong> : légumineuses, légumes frais, fruits, herbes et épices, oléagineux, fleurs",
            "<strong>Engrais</strong> de nouvelle génération, issus de matières renouvelables {{produits ou distribués ?}}",
        ],
        "liste_2": ("Ce que nous distribuons", ["Céréales, légumes surgelés et plats cuisinés"]),
        "encart": ("Pour les agriculteurs", "Nos agronomes vous accompagnent sur le terrain pour la fertilité des sols, le choix des engrais, et la lutte contre les maladies et les ravageurs."),
        "pour_qui": "Hôtels, restaurants, cantines, supermarchés, grossistes, éleveurs (poussins, aliments), exploitants agricoles (conseil, engrais).",
        "pourquoi": "{{nombre de têtes, d'œufs par jour, d'hectares}} et des contrôles sanitaires sur chaque lot {{vaccination, suivi vétérinaire : préciser}}.",
        "avec": [
            ("restauration-base-vie", "Nous cuisinons nos propres produits pour vos équipes."),
            ("logistique", "Livraisons régulières à vos cantines et à vos points de vente."),
            ("produits-hygiene", "Pour les cuisines et les sanitaires des établissements que nous livrons."),
        ],
        "bouton": "Demander un devis ou commander en gros",
        "seo": ("Porcs, œufs, poussins et légumes en RDC · GBIC", "Élevage, œufs, poussins d'un jour, aliments pour bétail et légumes produits au Congo, livrés en volume."),
    },
    {
        "slug": "produits-hygiene",
        "nom": "Produits d'hygiène",
        "famille": 2,
        "carte": "Papier toilette fabriqué {{au Congo}}, lingettes et couches pour adultes, en gros, pour hôtels, bureaux, restaurants et bases-vie.",
        "photo": "rouleaux-papier",
        "personne": "acheteur",
        "h1": "Du papier toilette fabriqué au Congo, livré en gros à vos établissements.",
        "chapo": "GBIC fabrique du papier toilette et distribue des lingettes et des couches pour adultes. Nos produits équipent des hôtels, des bureaux, des restaurants {{et des bases-vie}} en RDC, et partent à l'export ailleurs en Afrique {{pays et volumes à confirmer}}.",
        "titre_liste": "Ce que nous fabriquons",
        "liste": ["<strong>Papier toilette</strong> : absorbant, doux pour la peau, résistant, biodégradable"],
        "liste_2": ("Ce que nous distribuons", ["<strong>Lingettes humides</strong>", "<strong>Couches pour adultes</strong>"]),
        "pour_qui": "Hôtels, bureaux, restaurants, hôpitaux et cliniques {{à confirmer}}, bases-vie, grossistes et distributeurs.",
        "pourquoi": "Un rouleau fabriqué à {{ville}} ne passe pas la frontière. Vous attendez moins, et votre prix dépend moins du cours du dollar {{seulement si c'est vrai}}. {{capacité de production : rouleaux par mois}}",
        "avec": [
            ("restauration-base-vie", "Une base-vie équipée et nourrie par le même fournisseur."),
            ("logistique", "Votre stock gardé chez nous et livré quand il baisse."),
            ("agropastoral", "Œufs et produits frais pour vos cuisines."),
        ],
        "bouton": "Demander un tarif de gros",
        "seo": ("Papier toilette et hygiénique en gros, RDC · GBIC", "Papier toilette fabriqué en RDC, lingettes et couches pour adultes en gros pour hôtels, bureaux, restaurants et bases-vie."),
    },
]
PAR_SLUG = {m["slug"]: m for m in METIERS}
FAMILLES = {1: "Nous servons vos sites", 2: "Nous produisons au Congo"}

PAGES = {
    "index.html": ("accueil.html", "GBIC · Fournisseur des sites miniers, Lubumbashi, Kolwezi", "Matériaux, logistique, vivres, cantine, hygiène et sous-traitance minière pour vos sites, de Lubumbashi à Kolwezi. Entreprise congolaise.", ""),
    "a-propos.html": ("a-propos.html", "À propos de GBIC · Entreprise congolaise, Lubumbashi", "Créée à Lubumbashi, GBIC sert les sites miniers du Katanga et produit au Congo ce que le pays importe encore.", "a-propos"),
    "securite.html": ("securite.html", "Sécurité et HSE · GBIC", "Évaluation des risques, équipements contrôlés, droit d'arrêt : nos règles de sécurité sur chaque chantier.", "securite"),
    "devis.html": ("devis.html", "Demander un devis · GBIC Lubumbashi", "Décrivez votre besoin en trois lignes, nous vous répondons le jour même et vous envoyons un prix sous 48 h.", "devis"),
    "metiers/index.html": ("metiers.html", "Nos métiers · GBIC Lubumbashi", "Services miniers, génie civil et matériaux, logistique, restauration et base-vie, agropastoral et produits d'hygiène : ce dont un site a besoin, chez un seul fournisseur.", "metiers"),
}


# ---------- Outils ----------
def a_remplir(texte):
    return re.sub(r"\{\{(.+?)\}\}", lambda m: f'<span class="a-remplir" title="À fournir par GBIC">[{m.group(1)}]</span>', texte)


def conditions(texte):
    def garder(m):
        return m.group(2) if m.group(1) in BLOCS_AFFICHES else ""
    return re.sub(r"<!--si:([a-z-]+)-->(.*?)<!--/si:\1-->", garder, texte, flags=re.S)


def lien_whatsapp(texte=MESSAGE_WHATSAPP):
    from urllib.parse import quote
    return f"https://wa.me/{WHATSAPP}?text={quote(texte)}"


def fond(nom, R, alt="", vitesse="-0.35", classe="fond-photo", chargement="lazy"):
    return (f'<div class="{classe}" data-vitesse="{vitesse}" aria-hidden="{"true" if not alt else "false"}">'
            f'<img src="{R}assets/img/fonds/{nom}-1920.webp" srcset="{R}assets/img/fonds/{nom}-960.webp 960w, {R}assets/img/fonds/{nom}-1920.webp 1920w" '
            f'sizes="100vw" alt="{html.escape(alt)}" loading="{chargement}" decoding="async"></div>')


ICONE_WHATSAPP = ('<svg viewBox="0 0 32 32" aria-hidden="true" fill="currentColor"><path d="M16 3C8.8 3 3 8.6 3 15.6c0 2.5.8 4.9 2.1 6.9L3.6 29l6.8-1.7c1.7.9 3.6 1.4 5.6 1.4 7.2 0 13-5.6 13-12.6S23.2 3 16 3zm0 23.4c-1.8 0-3.6-.5-5.1-1.4l-.4-.2-4 1 1-3.8-.3-.4a10.4 10.4 0 0 1-1.8-5.9C5.4 9.9 10.1 5.3 16 5.3s10.6 4.6 10.6 10.4S21.9 26.4 16 26.4zm5.8-7.8c-.3-.2-1.9-.9-2.2-1-.3-.1-.5-.2-.7.2l-1 1.2c-.2.2-.4.2-.7.1-.3-.2-1.4-.5-2.6-1.6-1-.9-1.6-1.9-1.8-2.2-.2-.3 0-.5.1-.7l.5-.6.3-.5c.1-.2 0-.4 0-.6l-1-2.4c-.3-.6-.5-.5-.7-.5h-.6c-.2 0-.6.1-.9.4-.3.3-1.2 1.1-1.2 2.8s1.2 3.3 1.4 3.5c.2.2 2.4 3.6 5.8 5 .8.3 1.4.5 1.9.7.8.2 1.5.2 2.1.1.6-.1 1.9-.8 2.2-1.5.3-.7.3-1.4.2-1.5-.1-.2-.3-.3-.6-.4z"/></svg>')


def entete(R, actif):
    def lien(href, texte, cle):
        courant = ' aria-current="page"' if cle == actif else ""
        return f'<a href="{R}{href}"{courant}>{texte}</a>'
    return f"""<a class="aller-contenu" href="#contenu">Aller au contenu</a>
<header class="entete" data-entete>
  <div class="entete__in conteneur">
    <a class="entete__logo" href="{R}index.html" aria-label="GBIC, retour à l'accueil">
      <img class="logo-clair" src="{R}assets/img/logo/gbic-horizontal-inverse.svg" alt="" width="142" height="60">
      <img class="logo-fonce" src="{R}assets/img/logo/gbic-horizontal.svg" alt="" width="142" height="60">
    </a>
    <button class="entete__menu" type="button" aria-expanded="false" aria-controls="navigation"><span></span>Menu</button>
    <nav class="nav" id="navigation" aria-label="Navigation principale">
      {lien("a-propos.html", "À propos", "a-propos")}
      {lien("metiers/index.html", "Nos métiers", "metiers")}
      {lien("securite.html", "Sécurité", "securite")}
      <a class="bouton bouton--petit" href="{R}devis.html">Demander un devis</a>
    </nav>
  </div>
</header>"""


def pied(R):
    metiers = "\n".join(f'          <li><a href="{R}metiers/{m["slug"]}.html">{m["nom"]}</a></li>' for m in METIERS)
    return f"""<footer class="pied sur-sombre">
  <div class="conteneur">
    <div class="pied__haut">
      <div class="pied__marque">
        <img src="{R}assets/img/logo/gbic-horizontal-inverse.svg" alt="GBIC" width="160" height="68" loading="lazy">
        <strong>Global Business Investments Congo</strong>
        <p>Le fournisseur de vos sites, depuis Lubumbashi.</p>
      </div>
      <div>
        <h2>Nos métiers</h2>
        <ul>
{metiers}
        </ul>
      </div>
      <div>
        <h2>GBIC</h2>
        <ul>
          <li><a href="{R}a-propos.html">À propos</a></li>
          <li><a href="{R}securite.html">Sécurité</a></li>
          <li><a href="{R}devis.html">Demander un devis</a></li>
          <li><a href="#" data-dossier>Dossier fournisseur (PDF)</a> {{{{à fournir}}}}</li>
          <li>{{{{adresse}}}}, Lubumbashi</li>
          <li>{{{{téléphone}}}} · {{{{e-mail}}}}</li>
        </ul>
      </div>
    </div>
    <div class="pied__bas">
      <p class="ref">RCCM CD/LSH/RCCM/24-B-00513 · Id. Nat. 05-15500-N41308E · N° impôt A2414371Y</p>
      <p class="ref">© 2026 GBIC {{{{SARL / SARLU}}}} · Photos : Pexels · Minerais et camions : images générées</p>
    </div>
  </div>
</footer>
<a class="whatsapp" href="{lien_whatsapp()}" target="_blank" rel="noopener">{ICONE_WHATSAPP}<span>Devis sur WhatsApp</span></a>"""


def gabarit(R, titre, description, actif, corps):
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(titre)}</title>
<meta name="description" content="{html.escape(description)}">
<meta property="og:title" content="{html.escape(titre)}">
<meta property="og:description" content="{html.escape(description)}">
<meta property="og:type" content="website">
<meta property="og:locale" content="fr_FR">
<link rel="icon" href="{R}favicon.ico" sizes="48x48">
<link rel="icon" href="{R}favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="{R}apple-touch-icon.png">
<link rel="manifest" href="{R}site.webmanifest">
<meta name="theme-color" content="#14329A">
<link rel="preload" href="{R}assets/fonts/montserrat-latin-800-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{R}assets/fonts/inter-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{R}assets/css/style.css">
<script src="{R}assets/js/main.js" defer></script>
</head>
<body>
{entete(R, actif)}
<main id="contenu">
{corps}
</main>
{pied(R)}
</body>
</html>
"""


# ---------- Morceaux réutilisés ----------
def carte_metier(m, R, numero):
    return f"""<a class="carte-metier" href="{R}metiers/{m['slug']}.html" data-revele data-scene>
  <div class="carte-metier__visuel">
    <div class="carte-metier__photo"><img src="{R}assets/img/fonds/{m['photo']}-960.webp" alt="" loading="lazy" decoding="async" data-vitesse="-0.12"></div>
    <img class="carte-metier__personne" src="{R}assets/img/calques/{m['personne']}.webp" alt="" loading="lazy" decoding="async" data-vitesse="0.16">
    <span class="carte-metier__num ref">{numero:02d} · {FAMILLES[m['famille']]}</span>
  </div>
  <div class="carte-metier__corps">
    <h3>{m['nom']}</h3>
    <p>{m['carte']}</p>
    <span class="lien-fleche">Voir ce que nous fournissons</span>
  </div>
</a>"""


def familles_metiers(R):
    blocs = []
    numero = 1
    for f, nom in FAMILLES.items():
        cartes = []
        for m in METIERS:
            if m["famille"] == f:
                cartes.append(carte_metier(m, R, numero))
                numero += 1
        blocs.append(f"""<div class="famille">
  <div class="famille__titre"><span class="ref">Famille {f}</span><h3>{nom}</h3></div>
  <div class="cartes">
{chr(10).join(cartes)}
  </div>
</div>""")
    blocs.append("""<div class="famille">
  <div class="famille__titre"><span class="ref">Famille 3</span><h3>Autres activités</h3></div>
  <ul class="autres">
    <li><strong>Gestion hôtelière</strong> · Ouverture et gestion d'hôtels et de résidences en RDC. <em>En développement</em></li>
    <li><strong>Hydrocarbures</strong> · Appui à l'exploration pétrolière et gazière. <em>En développement</em></li>
  </ul>
</div>""")
    return "\n".join(blocs)


def carte_corridor():
    """Carte du corridor intégrée dans la page, classes préfixées pour ne pas déborder sur le site."""
    chemin = os.path.join(RACINE, "assets", "carte", "carte-corridor.svg")
    svg = open(chemin, encoding="utf-8").read()
    for c in ["route-fond", "vers-frontiere", "fond", "zm", "cd", "prov", "pays", "trajet", "camion", "ville", "info", "zone", "km"]:
        svg = re.sub(rf'(?<![-\w])\.{c}(?=[\s{{,.:])', f".gc-{c}", svg)
        svg = re.sub(rf'class="{c}"', f'class="gc-{c}"', svg)
    svg = svg.replace('id="titre-carte"', 'id="titre-carte-gc"').replace('id="desc-carte"', 'id="desc-carte-gc"')
    svg = svg.replace('aria-labelledby="titre-carte desc-carte"', 'aria-labelledby="titre-carte-gc desc-carte-gc"')
    # Le poste frontière s'allume à l'étape 2.
    svg = svg.replace('<path class="gc-vers-frontiere"', '<path class="gc-vers-frontiere gc-kasumbalesa"')
    svg = svg.replace('<circle cx="814.0" cy="570.9"', '<circle class="gc-kasumbalesa" cx="814.0" cy="570.9"')
    svg = svg.replace('class="gc-info" text-anchor="end">KASUMBALESA', 'class="gc-info gc-kasumbalesa" text-anchor="end">KASUMBALESA')
    svg = svg.replace('class="gc-info" text-anchor="start">96 KM', 'class="gc-info gc-kasumbalesa" text-anchor="start">96 KM')
    return svg


def page_metier(m):
    R = "../"
    liste = "\n".join(f"<li>{x}</li>" for x in m["liste"])
    bloc2 = ""
    if "liste_2" in m:
        titre2, items2 = m["liste_2"]
        bloc2 = f'<h3 class="sous-titre-liste">{titre2}</h3>\n<ul class="liste-fournie">' + "".join(f"<li>{x}</li>" for x in items2) + "</ul>"
    encart = ""
    if "encart" in m:
        encart = f'<div class="encadre"><h3>{m["encart"][0]}</h3><p>{m["encart"][1]}</p></div>'
    avec = "\n".join(
        f'<a href="{PAR_SLUG[s]["slug"]}.html" data-revele style="--delai:{i * 0.08:.2f}s"><h3>{PAR_SLUG[s]["nom"]}</h3><p>{phrase}</p><span class="lien-fleche">Voir le métier</span></a>'
        for i, (s, phrase) in enumerate(m["avec"]))
    corps = f"""<section class="page-hero sur-sombre" data-scene>
  {fond(m['photo'], R, chargement='eager')}
  <img class="page-hero__personne" src="{R}assets/img/calques/{m['personne']}.webp" alt="" data-vitesse="0.18" fetchpriority="high">
  <div class="conteneur">
    <div class="page-hero__texte">
      <p class="fil"><a href="{R}index.html">Accueil</a> / <a href="index.html">Nos métiers</a> / {m['nom']}</p>
      <p class="ref ref--point">{FAMILLES[m['famille']]}</p>
      <h1>{m['h1']}</h1>
      <p>{m['chapo']}</p>
      <div class="hero__actions"><a class="bouton" href="{R}devis.html?metier={m['slug']}">{m['bouton']} <span class="fleche" aria-hidden="true">→</span></a></div>
    </div>
  </div>
</section>

<section class="section">
  <div class="conteneur deux-col deux-col--etroit">
    <div data-revele>
      <p class="ref">01 · {m['titre_liste']}</p>
      <h2 style="margin-top:18px">{m['titre_liste']}</h2>
    </div>
    <div data-revele>
      <ul class="liste-fournie">
{liste}
      </ul>
      {bloc2}
      {('<div style="margin-top:32px">' + encart + '</div>') if encart else ''}
    </div>
  </div>
</section>

<section class="section section--brume">
  <div class="conteneur deux-col">
    <div class="encadre" data-revele><p class="ref" style="margin-bottom:12px">02 · Pour qui</p><p>{m['pour_qui']}</p></div>
    <div class="encadre" data-revele style="--delai:.1s"><p class="ref" style="margin-bottom:12px">03 · Pourquoi nous</p><p>{m['pourquoi']}</p></div>
  </div>
</section>

<section class="section">
  <div class="conteneur">
    <div class="entete-section" data-revele>
      <p class="ref">04 · Un seul fournisseur</p>
      <h2>Souvent commandé avec</h2>
    </div>
    <div class="avec">
{avec}
    </div>
  </div>
</section>

<section class="appel sur-sombre" data-scene>
  {fond('camions-piste', R)}
  <div class="conteneur">
    <h2 data-revele>Dites-nous ce qui manque sur votre site cette semaine.</h2>
    <p data-revele>Décrivez-le en trois lignes, nous revenons vers vous avec un prix.</p>
    <div class="appel__actions" data-revele><a class="bouton" href="{R}devis.html?metier={m['slug']}">{m['bouton']} <span class="fleche" aria-hidden="true">→</span></a></div>
  </div>
</section>"""
    return gabarit(R, m["seo"][0], m["seo"][1], "metiers", corps)


def finaliser(texte):
    return a_remplir(conditions(texte))


def main():
    os.makedirs(os.path.join(RACINE, "metiers"), exist_ok=True)
    variables_communes = {
        "WHATSAPP": lien_whatsapp(),
        "FORMULAIRE_ENVOI": FORMULAIRE_ENVOI,
        "CARTE_CORRIDOR": carte_corridor(),
    }
    for sortie, (source, titre, description, actif) in PAGES.items():
        R = "../" if "/" in sortie else ""
        corps = open(os.path.join(SRC, source), encoding="utf-8").read()
        variables = dict(variables_communes, R=R, FAMILLES_METIERS=familles_metiers(R))
        variables["COCHES_METIERS"] = "\n".join(
            f'<label class="coche"><input type="checkbox" name="metier" value="{m["slug"]}"> {m["nom"]}</label>' for m in METIERS
        ) + '\n<label class="coche"><input type="checkbox" name="metier" value="gestion-hoteliere"> Gestion hôtelière</label>' \
            + '\n<label class="coche"><input type="checkbox" name="metier" value="autre"> Autre</label>'
        corps = re.sub(r"\[\[([A-Z_]+)\]\]", lambda m: variables[m.group(1)], corps)
        page = finaliser(gabarit(R, titre, description, actif, corps))
        with open(os.path.join(RACINE, sortie), "w", encoding="utf-8", newline="\n") as f:
            f.write(page)
        print("écrit", sortie)
    for m in METIERS:
        sortie = f"metiers/{m['slug']}.html"
        with open(os.path.join(RACINE, sortie), "w", encoding="utf-8", newline="\n") as f:
            f.write(finaliser(page_metier(m)))
        print("écrit", sortie)


if __name__ == "__main__":
    main()
