/* GBIC · parallaxe et interactions. JavaScript pur, sans bibliothèque.
   - [data-vitesse] : calque qui se déplace plus vite (>0) ou plus lentement (<0) que la page,
     dans sa scène ([data-scene] le plus proche). Options : data-rotation (degrés), data-x (déplacement horizontal).
   - [data-route] : élément qui traverse sa scène de gauche à droite au fil du défilement.
   - [data-habitude] : carte du corridor pilotée par le défilement.
   - [data-revele] : apparition à l'entrée dans l'écran.
   Tout s'arrête si le visiteur a demandé moins de mouvement. */
(function () {
  "use strict";
  document.documentElement.classList.add("js");

  var reduit = window.matchMedia("(prefers-reduced-motion: reduce)");
  var bornes = function (v, min, max) { return Math.min(max, Math.max(min, v)); };

  /* ---------- En-tête : transparent sur le haut de page, solide ensuite ---------- */
  var entete = document.querySelector("[data-entete]");
  function majEntete() {
    if (entete) entete.classList.toggle("est-solide", window.scrollY > 40);
  }

  /* ---------- Menu téléphone ---------- */
  var boutonMenu = document.querySelector(".entete__menu");
  if (boutonMenu && entete) {
    boutonMenu.addEventListener("click", function () {
      var ouvert = entete.classList.toggle("menu-ouvert");
      boutonMenu.setAttribute("aria-expanded", String(ouvert));
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && entete.classList.contains("menu-ouvert")) {
        entete.classList.remove("menu-ouvert");
        boutonMenu.setAttribute("aria-expanded", "false");
        boutonMenu.focus();
      }
    });
  }

  /* ---------- Calques de parallaxe ---------- */
  var calques = Array.prototype.map.call(document.querySelectorAll("[data-vitesse], [data-route]"), function (el) {
    return {
      el: el,
      scene: el.closest("[data-scene]") || el.parentElement,
      vitesse: parseFloat(el.getAttribute("data-vitesse") || "0"),
      rotation: parseFloat(el.getAttribute("data-rotation") || "0"),
      x: parseFloat(el.getAttribute("data-x") || "0"),
      route: el.hasAttribute("data-route")
    };
  });

  // Seules les scènes visibles sont recalculées.
  var scenesVisibles = new Set();
  if ("IntersectionObserver" in window) {
    var obsScenes = new IntersectionObserver(function (entrees) {
      entrees.forEach(function (e) {
        if (e.isIntersecting) scenesVisibles.add(e.target); else scenesVisibles.delete(e.target);
      });
      demander();
    }, { rootMargin: "20% 0px" });
    calques.forEach(function (c) { obsScenes.observe(c.scene); });
  } else {
    calques.forEach(function (c) { scenesVisibles.add(c.scene); });
  }

  function majCalques(hauteurEcran) {
    calques.forEach(function (c) {
      if (!scenesVisibles.has(c.scene)) return;
      var r = c.scene.getBoundingClientRect();
      // 0 : la scène entre par le bas, 1 : elle sort par le haut.
      var p = bornes((hauteurEcran - r.top) / (hauteurEcran + r.height), 0, 1);
      if (c.route) {
        var largeur = c.scene.clientWidth;
        var q = bornes((p - 0.2) / 0.5, 0, 1);
        var depart = -c.el.offsetWidth * 0.6;
        var arrivee = largeur - c.el.offsetWidth * 0.55;
        c.el.style.transform = "translate3d(" + (depart + (arrivee - depart) * q).toFixed(1) + "px,0,0)";
        c.scene.style.setProperty("--avance", q.toFixed(3));
        var etapes = c.scene.querySelectorAll(".etapes li");
        etapes.forEach(function (li, i) { li.classList.toggle("est-atteinte", q >= (i + 0.35) / etapes.length); });
        return;
      }
      var centre = 0.5 - p;
      var y = centre * c.vitesse * hauteurEcran * 0.7;
      var x = centre * c.x * hauteurEcran * 0.5;
      var rot = -centre * c.rotation;
      c.el.style.transform = "translate3d(" + x.toFixed(1) + "px," + y.toFixed(1) + "px,0)" + (rot ? " rotate(" + rot.toFixed(2) + "deg)" : "");
    });
  }

  /* ---------- Le coût de l'habitude : la carte suit le défilement ---------- */
  var habitude = document.querySelector("[data-habitude]");
  var etapesHabitude = habitude ? habitude.querySelectorAll(".etape") : [];
  var compteur = habitude ? habitude.querySelectorAll(".habitude__compteur span") : [];
  var carte = habitude ? habitude.querySelector(".carte") : null;
  var modeBureau = window.matchMedia("(min-width: 901px)");

  function majHabitude(hauteurEcran) {
    if (!habitude || !carte) return;
    var r = habitude.getBoundingClientRect();
    var p;
    if (modeBureau.matches) {
      p = bornes(-r.top / (r.height - hauteurEcran), 0, 1);
      var index = Math.min(etapesHabitude.length - 1, Math.floor(p * etapesHabitude.length * 0.999));
      etapesHabitude.forEach(function (e, i) { e.classList.toggle("est-active", i === index); });
      compteur.forEach(function (s, i) { s.classList.toggle("est-active", i <= index); });
    } else {
      var rc = carte.getBoundingClientRect();
      p = bornes((hauteurEcran * 0.85 - rc.top) / (rc.height + hauteurEcran * 0.3), 0, 1);
      etapesHabitude.forEach(function (e) { e.classList.add("est-active"); });
    }
    // Étape 1 : rien. Étape 2 : la frontière s'allume. Étape 3 : le trajet se dessine jusqu'à Kolwezi.
    carte.style.setProperty("--frontiere", bornes((p - 0.25) / 0.2, 0, 1).toFixed(3));
    carte.style.setProperty("--trace", bornes((p - 0.55) / 0.4, 0, 1).toFixed(3));
  }

  /* ---------- Boucle ---------- */
  var enAttente = false;
  function maj() {
    enAttente = false;
    majEntete();
    if (reduit.matches) {
      if (carte) { carte.style.setProperty("--trace", "1"); carte.style.setProperty("--frontiere", "1"); }
      etapesHabitude.forEach(function (e) { e.classList.add("est-active"); });
      document.querySelectorAll(".etapes li").forEach(function (li) { li.classList.add("est-atteinte"); });
      return;
    }
    var h = window.innerHeight;
    majCalques(h);
    majHabitude(h);
  }
  function demander() {
    if (!enAttente) { enAttente = true; window.requestAnimationFrame(maj); }
  }
  window.addEventListener("scroll", demander, { passive: true });
  window.addEventListener("resize", demander);
  if (reduit.addEventListener) reduit.addEventListener("change", demander);
  demander();

  /* ---------- Apparition au défilement ---------- */
  var aReveler = document.querySelectorAll("[data-revele]");
  if ("IntersectionObserver" in window && !reduit.matches) {
    var obsRevele = new IntersectionObserver(function (entrees) {
      entrees.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add("est-visible"); obsRevele.unobserve(e.target); }
      });
    }, { rootMargin: "0px 0px -10% 0px" });
    aReveler.forEach(function (el) { obsRevele.observe(el); });
  } else {
    aReveler.forEach(function (el) { el.classList.add("est-visible"); });
  }

  /* ---------- Formulaire de devis ---------- */
  var formulaire = document.querySelector("[data-devis]");
  if (formulaire) {
    // Le bouton « Demander un devis » d'une page métier arrive avec ?metier=… : la case est déjà cochée.
    var demande = new URLSearchParams(window.location.search).get("metier");
    if (demande) {
      var caseMetier = formulaire.querySelector('input[name="metier"][value="' + demande.replace(/[^a-z-]/g, "") + '"]');
      if (caseMetier) caseMetier.checked = true;
    }

    var ok = formulaire.querySelector(".message--ok");
    var ko = formulaire.querySelector(".message--erreur");

    function verifier() {
      var valide = true;
      var groupe = formulaire.querySelector("fieldset[data-requis]");
      var coche = formulaire.querySelectorAll('input[name="metier"]:checked').length > 0;
      groupe.classList.toggle("est-en-erreur", !coche);
      if (!coche) valide = false;
      formulaire.querySelectorAll(".champ [required]").forEach(function (champ) {
        var bon = champ.checkValidity();
        champ.closest(".champ").classList.toggle("est-en-erreur", !bon);
        champ.setAttribute("aria-invalid", String(!bon));
        if (!bon) valide = false;
      });
      return valide;
    }

    formulaire.addEventListener("change", function (e) {
      if (e.target.name === "metier") formulaire.querySelector("fieldset[data-requis]").classList.remove("est-en-erreur");
    });

    formulaire.addEventListener("submit", function (e) {
      e.preventDefault();
      ok.classList.remove("est-visible");
      ko.classList.remove("est-visible");
      if (!verifier()) {
        var premier = formulaire.querySelector(".est-en-erreur input, .est-en-erreur textarea");
        if (premier) premier.focus();
        return;
      }
      var adresse = formulaire.getAttribute("data-envoi");
      if (!adresse) {
        // Pas encore de service d'envoi branché : on le dit plutôt que de faire semblant.
        ko.classList.add("est-visible");
        ko.focus();
        return;
      }
      var bouton = formulaire.querySelector('button[type="submit"]');
      bouton.disabled = true;
      fetch(adresse, { method: "POST", body: new FormData(formulaire), headers: { Accept: "application/json" } })
        .then(function (r) {
          if (!r.ok) throw new Error(r.status);
          formulaire.reset();
          ok.classList.add("est-visible");
          ok.focus();
        })
        .catch(function () { ko.classList.add("est-visible"); ko.focus(); })
        .then(function () { bouton.disabled = false; });
    });
  }
})();
