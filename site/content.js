/* =====================================================================
   CONTENU DU SITE — le seul fichier à modifier au quotidien
   ---------------------------------------------------------------------
   Tout le texte, les projets, les comparateurs et la galerie sont ici.
   Le code (assets/app.js) lit ce fichier et construit le site tout seul.

   Règles simples :
   - Un texte traduit s'écrit { fr: "…", en: "…" }.
   - Un champ vide ("") n'est PAS affiché sur le site : aucun trou visible.
     C'est voulu : on n'invente rien, on complète quand l'info arrive.
   - "// À COMPLÉTER" signale une information encore inconnue.
   - Les chemins des médias sont relatifs au dossier site/ (ex. "media/…").
   - Pour réordonner : déplacer un bloc { … } dans sa liste.
   - Pour supprimer : effacer le bloc { … } (et la virgule qui le suit).
   - Après une modification, recharger la page : rien à compiler.
   ===================================================================== */

window.SITE = {

  /* ---------- Identité ---------- */
  nom: "Momar Gaye",
  // Les rôles du grand titre d'accueil, écrits tels que Momar les a donnés.
  roles: ["FILMMAKER.", "VIDEO EDITOR.", "COLORIST."],
  logiciel: "DaVinci Resolve Studio",
  // Adresse publique du site (sert seulement au partage et au référencement).
  adresse: "https://thomas-soft.github.io/momar-portfolio/",

  /* ---------- Accueil : vidéo de fond plein écran ---------- */
  accueil: {
    video1080: "media/accueil/fond-1080.mp4", // ordinateur
    video720: "media/accueil/fond-720.mp4",   // téléphone et petite tablette
    poster: "media/accueil/fond-poster.jpg",  // image affichée pendant le chargement (ordinateur)
    poster720: "media/accueil/fond-poster-720.jpg" // la même, plus légère, pour les petits écrans
    // (si on change ces deux images, changer aussi les deux lignes « fond-poster » de index.html)
  },

  /* ---------- Showreel (30 à 60 s) ----------
     Vide pour l'instant : le site affiche « Showreel — bientôt ».
     Pour l'activer : mettre le chemin de la vidéo et de son image. */
  showreel: {
    video: "",  // À COMPLÉTER, ex. "media/showreel/showreel.mp4"
    poster: "", // À COMPLÉTER, ex. "media/showreel/poster.jpg"
    ratio: "16/9"
  },

  /* ---------- Réalisations (Selected Work) ----------
     L'ordre de la liste = l'ordre des cartes sur le site.
     Champs d'un projet :
       id          identifiant court, sans espace (sert à l'adresse #/projet/<id>)
       titre       { fr, en }
       categorie   "filmmaking", "editing" ou "color" (ou une liste : ["editing", "color"])
       role        { fr, en }  ex. { fr: "Montage", en: "Editor" }
       description { fr, en }  une ou deux phrases
       client, annee           texte libre
       technique   liste de lignes { label: { fr, en }, valeur: "…" }
                   ex. { label: { fr: "Caméra", en: "Camera" }, valeur: "Sony FX3" }
       miniature   image de la carte (16:9)
       apercu      vidéo muette courte jouée au survol de la carte
       extrait     extrait de 20 à 30 s, avec le son, joué dans la page projet
       integrale   version complète (laisser "" si la vidéo dure 30 s ou moins :
                   le bouton « Version intégrale » disparaît alors tout seul)
       poster      image affichée avant la lecture dans la page projet
       ratio       format du fichier vidéo, ex. "16/9" (le lecteur montre toujours l'image entière)
       cadre       seulement si la vidéo a des bandes noires sur les côtés : format de l'image
                   utile, ex. "1.372/1". La carte est alors recadrée sur l'image utile (sans
                   les bandes) ; le lecteur montre toujours le fichier entier. Sinon "".
       audio       false si la vidéo n'a pas de son (le bouton son disparaît), sinon true
  */
  projets: [
    {
      id: "wiss-hyrox",
      titre: { fr: "Wiss Hyrox", en: "Wiss Hyrox" },
      categorie: "",                    // À COMPLÉTER
      role: { fr: "Étalonnage", en: "Color grading" },  // étalonnage confirmé par Momar (21/11/2026) ; autres rôles : À COMPLÉTER
      description: { fr: "", en: "" },  // À COMPLÉTER
      client: "",                       // À COMPLÉTER
      annee: "",                        // À COMPLÉTER
      technique: [],                    // À COMPLÉTER
      miniature: "media/projets/wiss-hyrox/miniature.jpg",
      apercu: "media/projets/wiss-hyrox/apercu.mp4",
      extrait: "media/projets/wiss-hyrox/extrait.mp4",
      integrale: "media/projets/wiss-hyrox/integrale.mp4",
      poster: "media/projets/wiss-hyrox/poster.jpg",
      ratio: "16/9",
      cadre: "1.372/1",             // image utile entre deux bandes noires latérales
      audio: true,
    },
    {
      id: "timeline-1w",
      titre: { fr: "Timeline 1w", en: "Timeline 1w" },
      categorie: "",                    // À COMPLÉTER
      role: { fr: "Étalonnage", en: "Color grading" },  // étalonnage confirmé par Momar (21/11/2026) ; autres rôles : À COMPLÉTER
      description: { fr: "", en: "" },  // À COMPLÉTER
      client: "",                       // À COMPLÉTER
      annee: "",                        // À COMPLÉTER
      technique: [],                    // À COMPLÉTER
      miniature: "media/projets/timeline-1w/miniature.jpg",
      apercu: "media/projets/timeline-1w/apercu.mp4",
      extrait: "media/projets/timeline-1w/extrait.mp4",
      integrale: "media/projets/timeline-1w/integrale.mp4",
      poster: "media/projets/timeline-1w/poster.jpg",
      ratio: "16/9",
      cadre: "1.274/1",             // image utile entre deux bandes noires latérales
      audio: true,
    },
    {
      id: "disney",
      titre: { fr: "Disney", en: "Disney" },
      categorie: "",                    // À COMPLÉTER
      role: { fr: "Étalonnage", en: "Color grading" },  // étalonnage confirmé par Momar (21/11/2026) ; autres rôles : À COMPLÉTER
      description: { fr: "", en: "" },  // À COMPLÉTER
      client: "",                       // À COMPLÉTER
      annee: "",                        // À COMPLÉTER
      technique: [],                    // À COMPLÉTER
      miniature: "media/projets/disney/miniature.jpg",
      apercu: "media/projets/disney/apercu.mp4",
      extrait: "media/projets/disney/extrait.mp4",
      integrale: "media/projets/disney/integrale.mp4",
      poster: "media/projets/disney/poster.jpg",
      ratio: "16/9",
      cadre: "",
      audio: true,
    },
    {
      id: "wissem-2",
      titre: { fr: "Wissem 2", en: "Wissem 2" },
      categorie: "",                    // À COMPLÉTER
      role: { fr: "Étalonnage", en: "Color grading" },  // étalonnage confirmé par Momar (21/11/2026) ; autres rôles : À COMPLÉTER
      description: { fr: "", en: "" },  // À COMPLÉTER
      client: "",                       // À COMPLÉTER
      annee: "",                        // À COMPLÉTER
      technique: [],                    // À COMPLÉTER
      miniature: "media/projets/wissem-2/miniature.jpg",
      apercu: "media/projets/wissem-2/apercu.mp4",
      extrait: "media/projets/wissem-2/extrait.mp4",
      integrale: "",                    // vidéo de 22 s : l'extrait est la vidéo entière
      poster: "media/projets/wissem-2/poster.jpg",
      ratio: "16/9",
      cadre: "",
      audio: true,
    },
    {
      id: "timeline-1",
      titre: { fr: "Timeline 1", en: "Timeline 1" },
      categorie: "",                    // À COMPLÉTER
      role: { fr: "Étalonnage", en: "Color grading" },  // étalonnage confirmé par Momar (21/11/2026) ; autres rôles : À COMPLÉTER
      description: { fr: "", en: "" },  // À COMPLÉTER
      client: "",                       // À COMPLÉTER
      annee: "",                        // À COMPLÉTER
      technique: [],                    // À COMPLÉTER
      miniature: "media/projets/timeline-1/miniature.jpg",
      apercu: "media/projets/timeline-1/apercu.mp4",
      extrait: "media/projets/timeline-1/extrait.mp4",
      integrale: "media/projets/timeline-1/integrale.mp4",
      poster: "media/projets/timeline-1/poster.jpg",
      ratio: "16/9",
      cadre: "",
      audio: true,
    },
    {
      id: "marco",
      titre: { fr: "Marco", en: "Marco" },
      categorie: "",                    // À COMPLÉTER
      role: { fr: "Étalonnage", en: "Color grading" },  // étalonnage confirmé par Momar (21/11/2026) ; autres rôles : À COMPLÉTER
      description: { fr: "", en: "" },  // À COMPLÉTER
      client: "",                       // À COMPLÉTER
      annee: "",                        // À COMPLÉTER
      technique: [],                    // À COMPLÉTER
      miniature: "media/projets/marco/miniature.jpg",
      apercu: "media/projets/marco/apercu.mp4",
      extrait: "media/projets/marco/extrait.mp4",
      integrale: "media/projets/marco/integrale.mp4",
      poster: "media/projets/marco/poster.jpg",
      ratio: "16/9",
      cadre: "",
      audio: true,
    },
    {
      id: "maroc",
      titre: { fr: "Maroc", en: "Maroc" },
      categorie: "color",               // projet d'étalonnage (versions LOG et GRADED fournies)
      role: { fr: "Étalonnage", en: "Color grading" },
      description: { fr: "", en: "" },  // À COMPLÉTER
      client: "",                       // À COMPLÉTER
      annee: "",                        // À COMPLÉTER
      technique: [],                    // À COMPLÉTER (caméra, profil LOG…)
      miniature: "media/projets/maroc/miniature.jpg",
      apercu: "media/projets/maroc/apercu.mp4",
      extrait: "media/projets/maroc/extrait.mp4",
      integrale: "",                    // vidéo de 20 s : l'extrait est la vidéo entière
      poster: "media/projets/maroc/poster.jpg",
      ratio: "16/9",
      cadre: "",
      audio: false,                 // source sans son : pas de bouton son
    },
    {
      id: "training",
      titre: { fr: "Training", en: "Training" },
      categorie: "color",               // projet d'étalonnage (versions LOG et GRADED fournies)
      role: { fr: "Étalonnage", en: "Color grading" },
      description: { fr: "", en: "" },  // À COMPLÉTER
      client: "",                       // À COMPLÉTER
      annee: "",                        // À COMPLÉTER
      technique: [],                    // À COMPLÉTER (caméra, profil LOG…)
      miniature: "media/projets/training/miniature.jpg",
      apercu: "media/projets/training/apercu.mp4",
      extrait: "media/projets/training/extrait.mp4",
      integrale: "",                    // vidéo de 12 s : l'extrait est la vidéo entière
      poster: "media/projets/training/poster.jpg",
      ratio: "16/9",
      cadre: "",
      audio: false,                 // source sans son : pas de bouton son
    }
  ],

  /* ---------- Comparateurs LOG / GRADED ----------
     images : deux photogrammes du MÊME plan, pris à la même image exacte.
       projet  id du projet (le titre affiché vient de la liste des projets)
       log     image LOG telle quelle (aucune correction)
       graded  la même image étalonnée
       vignette petite image (384 × 216) pour la rangée de vignettes (sinon l'image graded sert)
       ratio   format des deux images (identique pour les deux)
     L'ordre de la liste = l'ordre des vignettes sous le comparateur. */
  comparateurs: {
    images: [
      { projet: "maroc", log: "media/comparateurs/maroc-1-log.jpg", graded: "media/comparateurs/maroc-1-graded.jpg", vignette: "media/comparateurs/maroc-1-vignette.jpg", ratio: "16/9" },
      { projet: "maroc", log: "media/comparateurs/maroc-2-log.jpg", graded: "media/comparateurs/maroc-2-graded.jpg", vignette: "media/comparateurs/maroc-2-vignette.jpg", ratio: "16/9" },
      { projet: "maroc", log: "media/comparateurs/maroc-3-log.jpg", graded: "media/comparateurs/maroc-3-graded.jpg", vignette: "media/comparateurs/maroc-3-vignette.jpg", ratio: "16/9" },
      { projet: "maroc", log: "media/comparateurs/maroc-4-log.jpg", graded: "media/comparateurs/maroc-4-graded.jpg", vignette: "media/comparateurs/maroc-4-vignette.jpg", ratio: "16/9" },
      { projet: "training", log: "media/comparateurs/training-1-log.jpg", graded: "media/comparateurs/training-1-graded.jpg", vignette: "media/comparateurs/training-1-vignette.jpg", ratio: "16/9" }
    ],

    /* videos : un seul fichier MP4 « empilé » par comparateur :
       LOG en haut, une bande noire, GRADED en bas (synchronisés par construction).
         largeur, hauteur  taille d'UNE des deux images (ex. 1280 × 720)
         bande             hauteur de la bande noire entre les deux, en pixels
         poster            image empilée de la même façon, affichée avant la lecture */
    videos: [
      { projet: "maroc", src: "media/comparateurs/maroc-video.mp4", poster: "media/comparateurs/maroc-video-poster.jpg", largeur: 1280, hauteur: 720, bande: 16 },
      { projet: "training", src: "media/comparateurs/training-video.mp4", poster: "media/comparateurs/training-video-poster.jpg", largeur: 1280, hauteur: 720, bande: 16 }
    ]
  },

  /* ---------- Galerie d'étalonnage ----------
     Seulement des images que Momar a étalonnées (il a confirmé le 21/11/2026 avoir fait
     l'étalonnage de tous ses projets).
     Tous les champs d'information sont facultatifs : vide = non affiché.
       image      chemin de l'image (export sRGB)
       projet     id du projet
       camera     ex. "Sony FX3"
       profilLog  ex. "S-Log3"
       direction  direction artistique, { fr, en }
       logiciel   logiciel d'étalonnage
       ratio      format de l'image */
  // Ordre = ordre d'affichage. Images des projets sans LOG : scripts/medias_projets.py (GALERIE) ;
  // Maroc et Training : scripts/medias_etalonnage.py. Caméra, profil LOG, direction : À COMPLÉTER.
  galerie: [
    { image: "media/galerie/marco-1.jpg", projet: "marco", camera: "", profilLog: "", direction: { fr: "", en: "" }, logiciel: "DaVinci Resolve Studio", ratio: "16/9" }, // ruelle de médina (83,25 s)
    { image: "media/galerie/maroc-1.jpg", projet: "maroc", camera: "", profilLog: "", direction: { fr: "", en: "" }, logiciel: "DaVinci Resolve Studio", ratio: "16/9" }, // caméra, profil LOG, direction : À COMPLÉTER
    { image: "media/galerie/wiss-hyrox-1.jpg", projet: "wiss-hyrox", camera: "", profilLog: "", direction: { fr: "", en: "" }, logiciel: "DaVinci Resolve Studio", ratio: "16/9" }, // athlètes au Grand Palais (44,5 s)
    { image: "media/galerie/disney-1.jpg", projet: "disney", camera: "", profilLog: "", direction: { fr: "", en: "" }, logiciel: "DaVinci Resolve Studio", ratio: "16/9" }, // Orbitron de Discoveryland (75,08 s)
    { image: "media/galerie/training-1.jpg", projet: "training", camera: "", profilLog: "", direction: { fr: "", en: "" }, logiciel: "DaVinci Resolve Studio", ratio: "16/9" }, // caméra, profil LOG, direction : À COMPLÉTER
    { image: "media/galerie/marco-2.jpg", projet: "marco", camera: "", profilLog: "", direction: { fr: "", en: "" }, logiciel: "DaVinci Resolve Studio", ratio: "16/9" }, // allée rouge et bambous (111,58 s)
    { image: "media/galerie/maroc-2.jpg", projet: "maroc", camera: "", profilLog: "", direction: { fr: "", en: "" }, logiciel: "DaVinci Resolve Studio", ratio: "16/9" }, // caméra, profil LOG, direction : À COMPLÉTER
    { image: "media/galerie/wissem-2-1.jpg", projet: "wissem-2", camera: "", profilLog: "", direction: { fr: "", en: "" }, logiciel: "DaVinci Resolve Studio", ratio: "16/9" }, // athlète allongé dans la salle (20,33 s)
    { image: "media/galerie/timeline-1w-1.jpg", projet: "timeline-1w", camera: "", profilLog: "", direction: { fr: "", en: "" }, logiciel: "DaVinci Resolve Studio", ratio: "16/9" }, // coureur sur la piste (13,04 s)
    { image: "media/galerie/training-2.jpg", projet: "training", camera: "", profilLog: "", direction: { fr: "", en: "" }, logiciel: "DaVinci Resolve Studio", ratio: "16/9" }, // caméra, profil LOG, direction : À COMPLÉTER
    { image: "media/galerie/timeline-1-1.jpg", projet: "timeline-1", camera: "", profilLog: "", direction: { fr: "", en: "" }, logiciel: "DaVinci Resolve Studio", ratio: "16/9" }, // contre-jour en terrasse (32,33 s)
    { image: "media/galerie/wiss-hyrox-2.jpg", projet: "wiss-hyrox", camera: "", profilLog: "", direction: { fr: "", en: "" }, logiciel: "DaVinci Resolve Studio", ratio: "16/9" }  // medecine-ball sous la verrière (51 s)
  ],

  /* ---------- À propos ----------
     Texte tiré uniquement de ce que Momar a écrit (cahier des charges, section 7).
     Un paragraphe par ligne de la liste. */
  apropos: {
    texte: {
      fr: [
        "Je suis vidéaste, monteur vidéo et étalonneur junior.",
        "Passionné par le cinéma, la narration visuelle, le montage et la création d'ambiances colorimétriques, je travaille notamment sur DaVinci Resolve Studio, pour le montage comme pour l'étalonnage.",
        "Je souhaite collaborer avec des marques, des créateurs, des réalisateurs, des agences et des sociétés de production."
      ],
      en: [
        "I'm a filmmaker, video editor and junior colorist.",
        "Passionate about cinema, visual storytelling, editing and crafting mood through color, I work with DaVinci Resolve Studio in particular, for both editing and color grading.",
        "I'm looking to collaborate with brands, creators, directors, agencies and production companies."
      ]
    },
    // Deux photogrammes pour le collage. "legende" = petit mot calligraphié (facultatif).
    images: [
      { src: "media/apropos-1.jpg", legende: "Marco" },       // photogramme de Marco (44,2 s)
      { src: "media/apropos-2.jpg", legende: "Timeline 1w" }  // photogramme de Timeline 1w (36,5 s)
    ]
  },

  /* ---------- Contact ----------
     Un champ vide n'est pas affiché.
     instagram, vimeo, youtube : une adresse, ou une liste d'adresses (affichées dans cet ordre,
       dans le contact et le pied de page). Pour Instagram, le @compte est tiré de l'adresse.
     formEndpoint : adresse d'un service d'envoi (Formspree, FormSubmit…).
       Vide = le formulaire ouvre la messagerie du visiteur avec le message prérempli. */
  contact: {
    email: "momar.95@live.fr",
    instagram: [      // envoyés par Momar le 21/11/2026
      "https://www.instagram.com/mo.shoooter",
      "https://www.instagram.com/momar.9"
    ],
    vimeo: "",        // À COMPLÉTER, ex. "https://vimeo.com/…"
    youtube: "",      // À COMPLÉTER, ex. "https://www.youtube.com/@…"
    formEndpoint: ""  // À COMPLÉTER plus tard, ex. "https://formspree.io/f/xxxxxxx"
  },

  /* ---------- Textes de l'interface (FR / EN) ---------- */
  ui: {
    fr: {
      metaTitle: "Momar Gaye — Filmmaker, monteur vidéo et étalonneur",
      metaDesc: "Portfolio de Momar Gaye : filmmaker, monteur vidéo et étalonneur sur DaVinci Resolve Studio. Réalisations, comparateurs LOG / GRADED et contact.",
      skip: "Aller au contenu",
      homeLink: "Momar Gaye — accueil",
      navMain: "Navigation principale",
      navMobile: "Navigation mobile",
      heroLabel: "Accueil",
      galleryLabel: "Galerie",
      navWork: "Réalisations",
      navColor: "Étalonnage",
      navAbout: "À propos",
      navContact: "Contact",
      menu: "Menu",
      close: "Fermer",
      langSwitch: "Langue",
      welcome: "bienvenue dans l'univers de",
      explore: "découvrir mon travail",
      scroll: "Défiler",
      showreelKicker: "Showreel",
      showreelScript: "The",
      showreelCaps: "SHOWREEL",
      showreelSoon: "Showreel — bientôt",
      workKicker: "Selected Work",
      workScript: "Mes",
      workCaps: "RÉALISATIONS",
      workIntro: "Des extraits courts pour découvrir le travail en quelques secondes. Ouvrez un projet pour la grande vidéo et, quand elle existe, la version intégrale.",
      viewProject: "Voir le projet",
      catFilmmaking: "Filmmaking",
      catEditing: "Montage",
      catColor: "Étalonnage",
      colorKicker: "Color Grading",
      colorScript: "Avant",
      colorCaps: "/ APRÈS",
      colorIntro: "Le même plan, à la même image : l'original en LOG, puis la version étalonnée. Faites glisser la barre pour comparer.",
      cmpImagesTitle: "Photogrammes",
      cmpVideoTitle: "En mouvement",
      cmpVideoIntro: "Les deux versions jouent ensemble, à l'image près, avec une seule commande de lecture.",
      cmpSlider: "Comparateur LOG / GRADED",
      cmpShowLog: "LOG",
      cmpShowHalf: "50 / 50",
      cmpShowGraded: "GRADED",
      cmpExpand: "Agrandir",
      cmpShrink: "Réduire",
      cmpFrame: "Plan",
      cmpChoose: "Choisir un photogramme",
      cmpSimple: "Mode simple",
      cmpFull: "Mode comparateur",
      cmpSimpleHint: "Mode simple : une version à la fois.",
      cmpSeeLog: "Voir LOG",
      cmpSeeGraded: "Voir GRADED",
      galleryScript: "Graded",
      galleryCaps: "FRAMES",
      galleryIntro: "Une sélection d'images étalonnées.",
      galleryOpen: "Agrandir l'image",
      lbCamera: "Caméra",
      lbLog: "Profil LOG",
      lbDirection: "Direction artistique",
      lbSoftware: "Logiciel",
      aboutKicker: "About",
      aboutScript: "À",
      aboutCaps: "PROPOS",
      aboutRoles: "Métiers",
      aboutRolesValue: "Filmmaker · Monteur vidéo · Étalonneur",
      aboutSoftware: "Logiciel",
      contactKicker: "Contact",
      contactTitle: "LET'S CREATE SOMETHING TOGETHER.",
      contactIntro: "Un projet, une idée, une collaboration : écrivez-moi.",
      contactEmail: "E-mail",
      contactSocial: "Réseaux",
      contactButton: "Me contacter",
      formName: "Nom",
      formEmail: "E-mail",
      formMessage: "Message",
      formSend: "Envoyer",
      formSendMail: "Écrire avec ma messagerie",
      formNoteMail: "Ce formulaire ouvre votre messagerie avec le message prérempli : vous l'envoyez vous-même.",
      formOpening: "Votre messagerie s'ouvre avec le message prérempli. Si rien ne s'ouvre, écrivez directement à",
      formSending: "Envoi en cours…",
      formOk: "Merci, votre message a bien été envoyé.",
      formError: "L'envoi n'a pas fonctionné. Vous pouvez écrire directement à",
      formRequired: "Merci de remplir les trois champs (avec un e-mail valide).",
      mailSubject: "Contact depuis le portfolio",
      projectExtract: "Extrait",
      projectFull: "Version intégrale",
      projectRole: "Rôle",
      projectCategory: "Catégorie",
      projectClient: "Client",
      projectYear: "Année",
      projectTech: "Informations techniques",
      projectPrev: "Projet précédent",
      projectNext: "Projet suivant",
      projectBack: "Retour aux réalisations",
      play: "Lecture",
      pause: "Pause",
      mute: "Couper le son",
      unmute: "Activer le son",
      fullscreen: "Plein écran",
      exitFullscreen: "Quitter le plein écran",
      seek: "Position de lecture",
      videoError: "Vidéo indisponible",
      imageError: "Image indisponible",
      prev: "Précédent",
      next: "Suivant",
      backToTop: "Haut de page",
      footerRoles: "Filmmaker · Video Editor · Colorist"
    },
    en: {
      metaTitle: "Momar Gaye — Filmmaker, Video Editor & Colorist",
      metaDesc: "Portfolio of Momar Gaye: filmmaker, video editor and colorist working in DaVinci Resolve Studio. Selected work, LOG / GRADED comparisons and contact.",
      skip: "Skip to content",
      homeLink: "Momar Gaye — home",
      navMain: "Main navigation",
      navMobile: "Mobile navigation",
      heroLabel: "Home",
      galleryLabel: "Gallery",
      navWork: "Work",
      navColor: "Color Grading",
      navAbout: "About",
      navContact: "Contact",
      menu: "Menu",
      close: "Close",
      langSwitch: "Language",
      welcome: "welcome to the work of",
      explore: "explore my work",
      scroll: "Scroll",
      showreelKicker: "Showreel",
      showreelScript: "The",
      showreelCaps: "SHOWREEL",
      showreelSoon: "Showreel — coming soon",
      workKicker: "Selected Work",
      workScript: "Selected",
      workCaps: "WORK",
      workIntro: "Short cuts to get a feel for the work in seconds. Open a project for the full-size video and, where available, the full version.",
      viewProject: "View project",
      catFilmmaking: "Filmmaking",
      catEditing: "Editing",
      catColor: "Color Grading",
      colorKicker: "Color Grading",
      colorScript: "Color",
      colorCaps: "GRADING",
      colorIntro: "Same shot, same frame: the original LOG footage, then the final grade. Drag the bar to compare.",
      cmpImagesTitle: "Stills",
      cmpVideoTitle: "In motion",
      cmpVideoIntro: "Both versions play together, frame-accurate, with a single set of playback controls.",
      cmpSlider: "LOG / GRADED comparison",
      cmpShowLog: "LOG",
      cmpShowHalf: "50 / 50",
      cmpShowGraded: "GRADED",
      cmpExpand: "Expand",
      cmpShrink: "Collapse",
      cmpFrame: "Shot",
      cmpChoose: "Choose a still",
      cmpSimple: "Simple mode",
      cmpFull: "Split view",
      cmpSimpleHint: "Simple mode: one version at a time.",
      cmpSeeLog: "Show LOG",
      cmpSeeGraded: "Show GRADED",
      galleryScript: "Graded",
      galleryCaps: "FRAMES",
      galleryIntro: "A selection of graded frames.",
      galleryOpen: "View full size",
      lbCamera: "Camera",
      lbLog: "LOG profile",
      lbDirection: "Look",
      lbSoftware: "Software",
      aboutKicker: "About",
      aboutScript: "About",
      aboutCaps: "ME",
      aboutRoles: "Disciplines",
      aboutRolesValue: "Filmmaker · Video Editor · Colorist",
      aboutSoftware: "Software",
      contactKicker: "Contact",
      contactTitle: "LET'S CREATE SOMETHING TOGETHER.",
      contactIntro: "A project, an idea, a collaboration: get in touch.",
      contactEmail: "Email",
      contactSocial: "Social",
      contactButton: "Get in touch",
      formName: "Name",
      formEmail: "Email",
      formMessage: "Message",
      formSend: "Send",
      formSendMail: "Write from my email app",
      formNoteMail: "This form opens your email app with the message ready to go: you send it yourself.",
      formOpening: "Your email app is opening with the message pre-filled. If nothing happens, write directly to",
      formSending: "Sending…",
      formOk: "Thank you, your message has been sent.",
      formError: "Sending failed. You can write directly to",
      formRequired: "Please fill in all three fields (with a valid email).",
      mailSubject: "Enquiry from the portfolio",
      projectExtract: "Excerpt",
      projectFull: "Full version",
      projectRole: "Role",
      projectCategory: "Category",
      projectClient: "Client",
      projectYear: "Year",
      projectTech: "Technical details",
      projectPrev: "Previous project",
      projectNext: "Next project",
      projectBack: "Back to work",
      play: "Play",
      pause: "Pause",
      mute: "Mute",
      unmute: "Unmute",
      fullscreen: "Fullscreen",
      exitFullscreen: "Exit fullscreen",
      seek: "Playback position",
      videoError: "Video unavailable",
      imageError: "Image unavailable",
      prev: "Previous",
      next: "Next",
      backToTop: "Back to top",
      footerRoles: "Filmmaker · Video Editor · Colorist"
    }
  }
};
