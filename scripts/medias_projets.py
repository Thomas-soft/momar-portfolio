#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
medias_projets.py : médias des projets du portfolio de Momar Gaye.

À lancer depuis n'importe où (les chemins partent du dossier du projet) :

  python3 -I scripts/medias_projets.py analyse    # ffprobe, bandes noires, plans, signatures, doublons
  python3 -I scripts/medias_projets.py planches   # planches d'images dans travail/planches/
  python3 -I scripts/medias_projets.py projets [id ...] [--force]   # apercu, extrait, integrale, poster, miniature
  python3 -I scripts/medias_projets.py fond [--force]               # vidéo de fond de l'accueil + posters
  python3 -I scripts/medias_projets.py posters-fond [--force]       # posters du fond seulement
  python3 -I scripts/medias_projets.py images [--force]             # apropos-1/2.jpg et og.jpg
  python3 -I scripts/medias_projets.py verifier   # contrôles ffprobe + couleur, écrit travail/medias-projets.json
  python3 -I scripts/medias_projets.py tout [--force]

Pour changer un moment : modifier les tableaux de données ci-dessous (en secondes,
dans la vidéo source), puis relancer la commande correspondante avec --force
(sans --force, un fichier déjà produit n'est pas refait : les médias sont figés).

Couleur : aucun LUT, aucun filtre, aucune correction.
Vidéos : H.264 High, yuv420p, faststart, étiquetées BT.709 x3, plage limitée (tv).
Images : PNG extrait avec in_range=tv / in_color_matrix=bt709, puis JPEG avec le
profil sRGB incorporé sans conversion des valeurs (sips --embedProfile, ou
cjpeg -icc pour les posters du fond ; jamais sips --matchTo).

Fichiers de travail (PNG, planches, analyses, journal) : dossier travail/.
"""

import json
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
TRAVAIL = RACINE / "travail"
ANALYSE = TRAVAIL / "analyse"
PLANCHES = TRAVAIL / "planches"
PNG = TRAVAIL / "png-projets"
TMP = TRAVAIL / "tmp-projets"
MEDIA = RACINE / "site" / "media"
JOURNAL = TRAVAIL / "medias-projets-ffmpeg.log"
SRGB = "/System/Library/ColorSync/Profiles/sRGB Profile.icc"

# ---------------------------------------------------------------------------
# 1. DONNÉES : les sources et les temps choisis (à modifier ici, puis relancer)
# ---------------------------------------------------------------------------

# Projets (id -> fichier source, version étalonnée, et titre).
PROJETS = {
    "disney":      {"fichier": "originaux/wetransfer-1/disney v1.mov",          "titre": "Disney"},
    "marco":       {"fichier": "originaux/wetransfer-1/marco.mov",              "titre": "Marco"},
    "timeline-1":  {"fichier": "originaux/wetransfer-1/Timeline 1.mov",         "titre": "Timeline 1"},
    "maroc":       {"fichier": "originaux/wetransfer-1/vlog maroc grade.mov",   "titre": "Maroc"},
    "training":    {"fichier": "originaux/wetransfer-1/training grade.mov",     "titre": "Training"},
    "timeline-1w": {"fichier": "originaux/wetransfer-2/Timeline 1w.mov",        "titre": "Timeline 1w"},
    "wiss-hyrox":  {"fichier": "originaux/wetransfer-2/wiss hyrox final 3.mov", "titre": "Wiss Hyrox"},
    "wissem-2":    {"fichier": "originaux/wetransfer-2/wissem 2.mov",           "titre": "Wissem 2"},
}

# Versions LOG : utilisées seulement comme témoin par la détection de doublons
# (une version LOG doit être reconnue comme le même montage que sa version étalonnée).
TEMOINS = {
    "maroc-log":    "originaux/wetransfer-1/vlog maroc log .mov",
    "training-log": "originaux/wetransfer-1/training log.mov",
}

# Doublons écartés (id -> raison). Résultat de « analyse » : aucun doublon de montage
# (Timeline 1 / Timeline 1w : 0 % d'images communes ; wiss hyrox final 3 / wissem 2 : 0 %).
DOUBLONS = {}

# Plans communs à deux projets (montages différents, les deux sont gardés).
MATIERE_COMMUNE = {
    "training": "reprend 3 plans de Timeline 1 (0-5,6 s, 5,6-9 s et ~18 s), avec un autre étalonnage",
    "maroc": "reprend 2 plans de Marco (~114-117 s et le plan fixe du jardin ~141-157 s)",
}

# Ordre d'affichage des cartes sur le site.
ORDRE = ["wiss-hyrox", "timeline-1w", "disney", "wissem-2", "timeline-1", "marco", "maroc", "training"]

# Moments choisis, en secondes dans la source.
#   extrait   : liste de passages (entrée, sortie). Un seul = passage continu.
#               None = vidéo entière (sources de 30 s ou moins).
#   apercu    : (entrée, sortie), 6 à 10 s, muet, 720p (survol des cartes).
#   poster    : instant de l'image du poster (1920 px de large).
#   miniature : instant de la miniature de carte (1280 px de large).
# Les entrées/sorties tombent sur des changements de plan détectés (scdet, voir
# travail/medias-projets-analyse.json) ; les instants de poster/miniature sont dans un plan.
MOMENTS = {
    # restaurant à contre-jour, Village, Discoveryland, pont au couchant, titre « Disney Journey »
    "disney":      {"extrait": [(59.125, 86.375)], "apercu": (74.75, 82.5),
                    "poster": 60.5, "miniature": 93.0},
    # terrasse au couchant, repas, silhouettes, thé versé, place Jemaa el-Fna, riad, piscine en contre-jour
    "marco":       {"extrait": [(33.583, 55.875)], "apercu": (35.167, 45.0),
                    "poster": 44.2, "miniature": 41.5},
    # gros plans en terrasse, écrans partagés, détails de table (après les plans repris dans Training)
    "timeline-1":  {"extrait": [(9.125, 34.917)], "apercu": (9.125, 17.583),
                    "poster": 11.5, "miniature": 24.0},
    "maroc":       {"extrait": None, "apercu": (0.0, 6.5), "poster": 3.0, "miniature": 1.0},
    "training":    {"extrait": None, "apercu": (0.0, 8.0), "poster": 3.0, "miniature": 3.0},
    # drone sur la piste, noir et blanc, banc, détails, contre-plongée ciel bleu, drone
    "timeline-1w": {"extrait": [(18.25, 42.792)], "apercu": (35.125, 42.792),
                    "poster": 36.5, "miniature": 41.0},
    # façade du Grand Palais, verrière, portique START, rameurs, coureurs ; se termine
    # à la fin d'une phrase de la voix off (sous-titre « Et je vais changer ma vie. »)
    "wiss-hyrox":  {"extrait": [(4.542, 31.167)], "apercu": (4.542, 11.75),
                    "poster": 5.5, "miniature": 11.2},
    "wissem-2":    {"extrait": None, "apercu": (4.958, 13.375), "poster": 15.5, "miniature": 6.0},
}

# Vidéo de fond de l'accueil : plans des versions étalonnées (id, entrée, sortie), dans l'ordre.
# Les bandes noires sont retirées (fond seulement). Le dernier plan revient
# sur le premier par un fondu enchaîné court (raccord de boucle).
FOND = [
    ("timeline-1w", 39.60, 42.75),   # drone : la piste d'athlétisme, le coureur seul
    ("disney",      59.20, 62.30),   # couple au restaurant, lumière de fenêtre
    ("wiss-hyrox",  14.72, 17.15),   # verrière du Grand Palais (avant le portique START)
    ("marco",      133.45, 137.60),  # porte rouge, le couple passe en contre-jour
    ("disney",      78.55, 82.40),   # pont au couchant, silhouettes (avant le titre)
]
FOND_FONDU = 0.5   # secondes de fondu enchaîné entre plans et pour la boucle
# Posters du fond (première image de la boucle) : qualité JPEG (cjpeg) par taille.
FOND_POSTERS = {"fond-poster.jpg": (1920, 1080, 82), "fond-poster-720.jpg": (1280, 720, 55)}

# À propos (2 photogrammes, recadrés sur l'image utile) et image de partage og.jpg
# (1200x630) : (id, instant).
APROPOS = [("marco", 44.2), ("timeline-1w", 36.5)]
OG = ("disney", 60.5)

# Débits des intégrales : CRF 22 avec un plafond par projet (fichiers < 95 Mo) ;
# deux passes à débit moyen si la taille dépasse INTEGRALE_MAX_OCTETS.
INTEGRALE_CRF = 22
INTEGRALE_PLAFOND = {          # kb/s vidéo (maxrate), bufsize = 2x
    "disney": 5000, "marco": 4400, "timeline-1": 6000,
    "timeline-1w": 6000, "wiss-hyrox": 5000,
}
INTEGRALE_MAX_OCTETS = 90 * 1024 * 1024
EXTRAIT_CRF, EXTRAIT_PLAFOND = 20, 6000
APERCU_CRF, APERCU_PLAFOND = 25, 2500
FOND_CRF = {"1080": (24, 3200), "720": (23, 2000)}
AUDIO = ["-c:a", "aac", "-b:a", "192k", "-ac", "2", "-ar", "48000"]
COULEUR = ["-color_primaries", "bt709", "-color_trc", "bt709",
           "-colorspace", "bt709", "-color_range", "tv"]

# ---------------------------------------------------------------------------
# 2. OUTILS
# ---------------------------------------------------------------------------


def chemin(rel):
    return RACINE / rel


def journal(msg):
    TRAVAIL.mkdir(exist_ok=True)
    with open(JOURNAL, "a", encoding="utf-8") as f:
        f.write(time.strftime("%H:%M:%S ") + msg + "\n")


def lancer(cmd, sortie_texte=False):
    """Lance une commande ; la sortie bavarde va dans le journal."""
    journal("$ " + " ".join(str(c) for c in cmd))
    if sortie_texte:
        r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
        if r.returncode != 0:
            journal(r.stderr[-4000:])
            raise SystemExit(f"Échec : {cmd[0]} (voir {JOURNAL})")
        return r.stdout
    with open(JOURNAL, "a", encoding="utf-8") as f:
        r = subprocess.run([str(c) for c in cmd], stdout=f, stderr=f)
    if r.returncode != 0:
        raise SystemExit(f"Échec : {cmd[0]} (voir {JOURNAL})")


def sonder(fichier):
    out = lancer(["ffprobe", "-v", "error", "-show_format", "-show_streams",
                  "-of", "json", fichier], sortie_texte=True)
    return json.loads(out)


def resume_sonde(fichier):
    d = sonder(fichier)
    v = next(s for s in d["streams"] if s["codec_type"] == "video")
    a = next((s for s in d["streams"] if s["codec_type"] == "audio"), None)
    return {
        "duree": round(float(d["format"]["duration"]), 3),
        "octets": int(d["format"]["size"]),
        "debit_kbps": round(int(d["format"].get("bit_rate", 0)) / 1000),
        "largeur": v["width"], "hauteur": v["height"],
        "ips": v.get("r_frame_rate"), "images": int(v.get("nb_frames", 0) or 0),
        "codec": v["codec_name"], "profil": v.get("profile"), "pix_fmt": v.get("pix_fmt"),
        "primaries": v.get("color_primaries"), "trc": v.get("color_transfer"),
        "matrice": v.get("color_space"), "plage": v.get("color_range"),
        "audio": (f'{a["codec_name"]} {a.get("sample_rate")} Hz {a.get("channels")} can.'
                  if a else None),
        "audio_kbps": (round(int(a["bit_rate"]) / 1000) if a and a.get("bit_rate") else None),
    }


def toutes_sources():
    s = {k: v["fichier"] for k, v in PROJETS.items()}
    s.update(TEMOINS)
    return s


# ---------------------------------------------------------------------------
# 3. ANALYSE : ffprobe, bandes noires, plans, signatures d'images, doublons
# ---------------------------------------------------------------------------

SIG_L, SIG_H = 32, 18     # signature : image réduite à 32x18 en niveaux de gris
CAR = 18                  # 2e signature : carré central (hauteur x hauteur) réduit à 18x18,
                          # insensible aux bandes noires et aux recadrages 16:9 -> 4:3


def analyser_une(ident, rel, force=False):
    ANALYSE.mkdir(parents=True, exist_ok=True)
    meta = ANALYSE / f"{ident}-meta.txt"
    sig = ANALYSE / f"{ident}.gray"
    res = ANALYSE / f"{ident}.json"
    if res.exists() and sig.exists() and not force:
        return json.loads(res.read_text())
    src = chemin(rel)
    carre = ANALYSE / f"{ident}-carre.gray"
    fc = (f"[0:v]split=3[a][b][c];"
          f"[a]cropdetect=limit=24:round=2:reset=1,scale=480:270,scdet=threshold=10,"
          f"metadata=print:file='{meta}'[o1];"
          f"[b]scale={SIG_L}:{SIG_H}:flags=area,format=gray[o2];"
          f"[c]crop=ih:ih,scale={CAR}:{CAR}:flags=area,format=gray[o3]")
    lancer(["ffmpeg", "-nostdin", "-hide_banner", "-v", "error", "-hwaccel", "videotoolbox",
            "-i", src, "-filter_complex", fc,
            "-map", "[o1]", "-f", "null", "-",
            "-map", "[o2]", "-f", "rawvideo", "-y", sig,
            "-map", "[o3]", "-f", "rawvideo", "-y", carre])
    # lecture des métadonnées par image
    images, cur = [], None
    for ligne in meta.read_text().splitlines():
        if ligne.startswith("frame:"):
            parts = ligne.split()
            cur = {"t": float(parts[2].split(":")[1])}
            images.append(cur)
        elif "=" in ligne and cur is not None:
            k, v = ligne.split("=", 1)
            cur[k.split(".")[-1]] = float(v)
    # bandes noires : mode des cadres détectés sur les images non sombres
    cadres = {}
    for im in images:
        if "w" in im and im["w"] > 64 and im["h"] > 64:
            c = (int(im["w"]), int(im["h"]), int(im["x"]), int(im["y"]))
            cadres[c] = cadres.get(c, 0) + 1
    cadre = max(cadres.items(), key=lambda kv: kv[1])[0] if cadres else None
    part = round(cadres.get(cadre, 0) / max(1, len(images)), 3) if cadre else 0
    plans = [round(im["t"], 3) for im in images if im.get("score", 0) >= 10]
    sonde = resume_sonde(src)
    out = {
        "id": ident, "fichier": rel, "sonde": sonde,
        "cadre_utile": ({"w": cadre[0], "h": cadre[1], "x": cadre[2], "y": cadre[3],
                         "ratio": round(cadre[0] / cadre[1], 3),
                         "part_des_images": part} if cadre else None),
        "cadres_frequents": sorted(([list(k), n] for k, n in cadres.items()),
                                   key=lambda kv: -kv[1])[:5],
        "changements_de_plan": plans,
        "scores": [round(im.get("score", 0), 2) for im in images],
    }
    res.write_text(json.dumps(out, ensure_ascii=False))
    return out


def lire_signatures(ident, carre=False):
    if carre:
        data, larg, haut = (ANALYSE / f"{ident}-carre.gray").read_bytes(), CAR, CAR
    else:
        data, larg, haut = (ANALYSE / f"{ident}.gray").read_bytes(), SIG_L, SIG_H
    n = larg * haut
    return [data[i:i + n] for i in range(0, len(data) - n + 1, n)], larg, haut


def empreinte(sig, larg, haut):
    """Empreinte binaire par gradients (robuste à l'étalonnage : seul le signe
    des écarts entre pixels voisins compte). 32x18 -> 1102 bits, 18x18 -> 612 bits."""
    bits = 0
    for y in range(haut):
        row = y * larg
        for x in range(larg - 1):
            bits = (bits << 1) | (sig[row + x] > sig[row + x + 1])
    for y in range(haut - 1):
        row = y * larg
        for x in range(larg):
            bits = (bits << 1) | (sig[row + x] > sig[row + larg + x])
    return bits


def empreintes(ident, carre=False):
    sigs, larg, haut = lire_signatures(ident, carre)
    nb = (larg - 1) * haut + larg * (haut - 1)
    return [empreinte(x, larg, haut) for x in sigs], nb


def plus_longue_suite_croissante(vals):
    import bisect
    fins = []
    for v in vals:
        k = bisect.bisect_right(fins, v)
        if k == len(fins):
            fins.append(v)
        else:
            fins[k] = v
    return len(fins)


def comparer(a_emp, b_emp, nb_bits, pas=6, seuil_pct=12):
    """Pour une image sur `pas` de A, cherche l'image la plus proche dans B
    (distance de Hamming entre empreintes).
    - part_retrouvee : images de A dont le plus proche voisin dans B diffère de
      moins de `seuil_pct` % des bits ;
    - part_dans_l_ordre : plus longue suite de ces correspondances qui avance dans
      le même ordre dans B (même montage = mêmes images dans le même ordre)."""
    seuil = int(nb_bits * seuil_pct / 100)
    meilleurs = []
    for i in range(0, len(a_emp), pas):
        ea = a_emp[i]
        best_j, best_d = -1, nb_bits
        for j, eb in enumerate(b_emp):
            d = (ea ^ eb).bit_count()
            if d < best_d:
                best_d, best_j = d, j
        meilleurs.append((i, best_j, best_d))
    dists = [d for _, _, d in meilleurs]
    trouves = [(i, j) for i, j, d in meilleurs if d <= seuil]
    lis = plus_longue_suite_croissante([j for _, j in trouves])
    n = max(1, len(meilleurs))
    return {
        "images_testees": len(meilleurs),
        "distance_mediane_pct": round(100 * statistics.median(dists) / nb_bits, 1),
        "part_retrouvee_pct": round(100 * len(trouves) / n, 1),
        "part_dans_l_ordre_pct": round(100 * lis / n, 1),
    }


def correspondances(a, b, pas=24, carre=False):
    """Suite (temps A, meilleur temps B, distance %) une image par seconde."""
    ea, nb = empreintes(a, carre)
    eb, _ = empreintes(b, carre)
    out = []
    for i in range(0, len(ea), pas):
        best_j, best_d = -1, nb
        for j, e in enumerate(eb):
            d = (ea[i] ^ e).bit_count()
            if d < best_d:
                best_d, best_j = d, j
        out.append((round(i / 24, 2), round(best_j / 24, 2), round(100 * best_d / nb, 1)))
    return out


def cmd_analyse(force=False):
    sources = toutes_sources()
    infos = {}
    for ident, rel in sources.items():
        print(f"analyse {ident} …", flush=True)
        infos[ident] = analyser_une(ident, rel, force)
    print("empreintes …", flush=True)
    emp = {k: empreintes(k) for k in sources}
    empc = {k: empreintes(k, carre=True) for k in sources}
    paires = {}
    ids = list(sources)
    for ia, a in enumerate(ids):
        for b in ids[ia + 1:]:
            paires[f"{a} | {b}"] = {
                "image_entiere": {"a_dans_b": comparer(emp[a][0], emp[b][0], emp[a][1]),
                                  "b_dans_a": comparer(emp[b][0], emp[a][0], emp[a][1])},
                "carre_central": {"a_dans_b": comparer(empc[a][0], empc[b][0], empc[a][1]),
                                  "b_dans_a": comparer(empc[b][0], empc[a][0], empc[a][1])},
            }
    detail = {
        "timeline-1 | timeline-1w (carré central)": correspondances("timeline-1", "timeline-1w", carre=True),
        "wissem-2 | wiss-hyrox (carré central)": correspondances("wissem-2", "wiss-hyrox", carre=True),
        "training | timeline-1": correspondances("training", "timeline-1"),
        "maroc | marco": correspondances("maroc", "marco"),
        "maroc | maroc-log (témoin)": correspondances("maroc", "maroc-log"),
    }
    out = {"sources": infos, "paires": paires, "correspondances_1_par_s": detail,
           "methode": ("deux signatures par image : image entière réduite à 32x18 et carré "
                       "central (hauteur x hauteur, insensible aux bandes noires) réduit à 18x18, "
                       "en niveaux de gris ; empreinte binaire = signe des écarts entre pixels "
                       "voisins (robuste à l'étalonnage). Pour 1 image sur 6 de A, image la plus "
                       "proche dans B (distance de Hamming) ; retrouvée si < 12 % de bits "
                       "différents ; même montage si les correspondances avancent dans le même "
                       "ordre (plus longue suite croissante).")}
    (TRAVAIL / "medias-projets-analyse.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1))
    # résumé court à l'écran
    for k, v in infos.items():
        s, c = v["sonde"], v["cadre_utile"]
        print(f'{k:13s} {s["duree"]:7.2f}s {s["largeur"]}x{s["hauteur"]} {s["profil"]:5s} '
              f'plage={s["plage"]} plans={len(v["changements_de_plan"])} '
              f'cadre={c["w"]}x{c["h"]}+{c["x"]}+{c["y"]} r={c["ratio"]} ({c["part_des_images"]})')
    print("paires (retrouvée % / dans l'ordre %), image entière puis carré central, A->B | B->A :")
    for k, v in paires.items():
        e, c = v["image_entiere"], v["carre_central"]
        vals = [e["a_dans_b"], e["b_dans_a"], c["a_dans_b"], c["b_dans_a"]]
        txt = "  ".join(f'{x["part_retrouvee_pct"]:5.1f}/{x["part_dans_l_ordre_pct"]:5.1f}' for x in vals)
        print(f"  {k:28s} {txt}")


# ---------------------------------------------------------------------------
# 4. PLANCHES D'IMAGES (travail/planches/)
# ---------------------------------------------------------------------------


def cmd_planches(pas=1.0, force=False):
    PLANCHES.mkdir(parents=True, exist_ok=True)
    for ident, p in PROJETS.items():
        src = chemin(p["fichier"])
        duree = resume_sonde(src)["duree"]
        n = int(duree / pas) + 1
        col = 10
        par_planche = col * 6   # 60 vignettes par planche
        for k in range(0, n, par_planche):
            # pas de texte sur les vignettes (ffmpeg sans drawtext) : la vignette
            # en ligne L, colonne C (à partir de 0) est à debut + (L*10 + C) * pas secondes,
            # et debut est dans le nom du fichier.
            sortie = PLANCHES / f"{ident}-{k // par_planche + 1}-a-partir-de-{int(k * pas)}s.jpg"
            if sortie.exists() and not force:
                continue
            debut = k * pas
            nb = min(par_planche, n - k)
            lignes = (nb + col - 1) // col
            vf = (f"fps=1/{pas},"
                  f"scale=192:108:in_range=tv:in_color_matrix=bt709,"
                  f"tile={col}x{lignes}:padding=2:color=black")
            lancer(["ffmpeg", "-nostdin", "-hide_banner", "-v", "error", "-hwaccel", "videotoolbox",
                    "-ss", str(debut), "-t", str(nb * pas), "-i", src,
                    "-vf", vf, "-frames:v", "1", "-q:v", "4", "-y", sortie])
            print("planche", sortie.name, flush=True)


# ---------------------------------------------------------------------------
# 5. PRODUCTION (vidéos et images)
# ---------------------------------------------------------------------------

def x264(crf, maxrate_k, preset="slow"):
    return ["-c:v", "libx264", "-preset", preset, "-profile:v", "high", "-pix_fmt", "yuv420p",
            "-crf", str(crf), "-maxrate", f"{maxrate_k}k", "-bufsize", f"{2 * maxrate_k}k",
            "-g", "48", "-x264-params", "aq-mode=3", "-movflags", "+faststart",
            "-map_metadata", "-1", "-map_chapters", "-1", "-write_tmcd", "0", *COULEUR]


def echelle(largeur):
    # redimensionnement seul (pas de conversion de matrice ni de plage)
    return (f"scale={largeur}:-2:flags=lanczos:in_range=tv:out_range=tv:"
            f"in_color_matrix=bt709:out_color_matrix=bt709")


def source_muette(src):
    """True si la piste son de la source est un silence numérique (max <= -90 dB) :
    l'extrait est alors produit sans piste son."""
    out = subprocess.run(["ffmpeg", "-nostdin", "-v", "info", "-i", str(src), "-map", "0:a:0",
                          "-af", "volumedetect", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    for ligne in out.splitlines():
        if "max_volume:" in ligne:
            return float(ligne.split("max_volume:")[1].split()[0]) <= -90.0
    return True


def a_faire(sortie, force):
    if sortie.exists() and not force:
        print("  déjà fait (figé) :", sortie.relative_to(RACINE))
        return False
    sortie.parent.mkdir(parents=True, exist_ok=True)
    return True


def extraire_png(src, t, png, largeur=None, crop=None):
    vf = []
    if crop:
        vf.append(f"crop={crop['w']}:{crop['h']}:{crop['x']}:{crop['y']}")
    s = f"scale={largeur or 'iw'}:-2:flags=lanczos" if largeur else "scale=iw:ih"
    vf.append(s + ":in_range=tv:in_color_matrix=bt709")
    png.parent.mkdir(parents=True, exist_ok=True)
    lancer(["ffmpeg", "-nostdin", "-hide_banner", "-v", "error", "-ss", f"{t:.3f}", "-i", src,
            "-frames:v", "1", "-vf", ",".join(vf), "-pix_fmt", "rgb24", "-y", png])


def png_vers_jpeg(png, jpg, qualite=90):
    jpg.parent.mkdir(parents=True, exist_ok=True)
    # un seul appel : encodage JPEG + profil sRGB incorporé, sans conversion des valeurs
    # (deux appels recompresseraient le JPEG une 2e fois)
    lancer(["sips", "-s", "format", "jpeg", "-s", "formatOptions", str(qualite),
            "--embedProfile", SRGB, png, "--out", jpg])


def image(src, t, jpg, largeur=None, crop=None, force=False):
    if not a_faire(jpg, force):
        return
    png = PNG / (jpg.parent.name + "-" + jpg.stem + ".png")
    extraire_png(src, t, png, largeur, crop)
    png_vers_jpeg(png, jpg)
    print("  image", jpg.relative_to(RACINE))


def encoder_passages(src, passages, sortie, largeur, crf, maxrate, son=True, preset="slow",
                     entier=False):
    """Encode un ou plusieurs passages (entrée, sortie) mis bout à bout.
    Coupes franches à l'image (sur des changements de plan existants) ; fondus son
    de 0,3 s à chaque raccord et aux deux bouts d'un extrait (pas si `entier`)."""
    F = 0.3
    if len(passages) == 1:
        a, b = passages[0]
        d = b - a
        cmd = ["ffmpeg", "-nostdin", "-hide_banner", "-v", "error"]
        if not entier:
            cmd += ["-ss", f"{a:.3f}", "-t", f"{d:.3f}"]
        cmd += ["-i", src, "-map", "0:v:0", "-vf", echelle(largeur)]
        if son:
            cmd += ["-map", "0:a:0"]
            if not entier:
                cmd += ["-af", f"afade=t=in:st=0:d={F},afade=t=out:st={d - F:.3f}:d={F}"]
            cmd += AUDIO
        else:
            cmd += ["-an"]
        lancer(cmd + [*x264(crf, maxrate, preset), "-y", sortie])
        return
    fc, labels = [], []
    for i, (a, b) in enumerate(passages):
        d = b - a
        fc.append(f"[0:v]trim=start={a}:end={b},setpts=PTS-STARTPTS,{echelle(largeur)}[v{i}]")
        if son:
            chain = [f"atrim=start={a}:end={b}", "asetpts=PTS-STARTPTS",
                     f"afade=t=in:st=0:d={F}", f"afade=t=out:st={d - F:.3f}:d={F}"]
            fc.append(f"[0:a]{','.join(chain)}[a{i}]")
            labels.append(f"[v{i}][a{i}]")
        else:
            labels.append(f"[v{i}]")
    n = len(passages)
    if son:
        fc.append("".join(labels) + f"concat=n={n}:v=1:a=1[v][a]")
        maps = ["-map", "[v]", "-map", "[a]", *AUDIO]
    else:
        fc.append("".join(labels) + f"concat=n={n}:v=1:a=0[v]")
        maps = ["-map", "[v]", "-an"]
    lancer(["ffmpeg", "-nostdin", "-hide_banner", "-v", "error", "-i", src,
            "-filter_complex", ";".join(fc), *maps, *x264(crf, maxrate, preset),
            "-y", sortie])


def encoder_integrale(ident, src, sortie, duree):
    plafond = INTEGRALE_PLAFOND.get(ident, 5000)
    tmp = sortie.with_suffix(".tmp.mp4")
    lancer(["ffmpeg", "-nostdin", "-hide_banner", "-v", "error", "-i", src,
            "-map", "0:v:0", "-map", "0:a:0", "-vf", echelle(1920),
            *x264(INTEGRALE_CRF, plafond), *AUDIO, "-y", tmp])
    if tmp.stat().st_size > INTEGRALE_MAX_OCTETS:
        # deux passes à débit moyen calculé pour tenir sous la limite
        cible = int((INTEGRALE_MAX_OCTETS * 8 / duree) / 1000 * 0.95) - 192
        cible = min(cible, plafond)
        print(f"  {ident} : trop lourd ({tmp.stat().st_size} o), 2 passes à {cible} kb/s")
        TMP.mkdir(parents=True, exist_ok=True)
        log = TMP / f"{ident}-2pass"
        base = ["ffmpeg", "-nostdin", "-hide_banner", "-v", "error", "-i", src,
                "-map", "0:v:0", "-vf", echelle(1920), "-c:v", "libx264", "-preset", "slow",
                "-profile:v", "high", "-pix_fmt", "yuv420p", "-b:v", f"{cible}k",
                "-maxrate", f"{int(cible * 1.5)}k", "-bufsize", f"{cible * 3}k", "-g", "48",
                "-x264-params", "aq-mode=3", "-map_metadata", "-1", "-write_tmcd", "0",
                *COULEUR, "-passlogfile", log]
        lancer(base + ["-pass", "1", "-an", "-f", "mp4", "-y", "/dev/null"])
        lancer(base[:9] + ["-map", "0:a:0"] + base[9:] +
               ["-pass", "2", *AUDIO, "-movflags", "+faststart", "-y", tmp])
    tmp.replace(sortie)


def cmd_projets(ids=None, force=False):
    for ident in (ids or PROJETS):
        if ident in DOUBLONS:
            print(f"{ident} : doublon écarté, rien à produire")
            continue
        p, m = PROJETS[ident], MOMENTS[ident]
        src = chemin(p["fichier"])
        duree = resume_sonde(src)["duree"]
        dossier = MEDIA / "projets" / ident
        print(f"{ident} :", flush=True)
        s = dossier / "apercu.mp4"
        if a_faire(s, force):
            encoder_passages(src, [m["apercu"]], s, 1280, APERCU_CRF, APERCU_PLAFOND, son=False)
            print("  apercu.mp4")
        s = dossier / "extrait.mp4"
        if a_faire(s, force):
            passages = m["extrait"] or [(0, duree)]
            encoder_passages(src, passages, s, 1920, EXTRAIT_CRF, EXTRAIT_PLAFOND,
                             son=not source_muette(src), entier=m["extrait"] is None)
            print("  extrait.mp4")
        s = dossier / "integrale.mp4"
        if duree > 30.5:
            if a_faire(s, force):
                encoder_integrale(ident, src, s, duree)
                print("  integrale.mp4")
        elif s.exists():
            s.unlink()
        image(src, m["poster"], dossier / "poster.jpg", 1920, force=force)
        image(src, m["miniature"], dossier / "miniature.jpg", 1280, force=force)


def cadre_utile(ident):
    f = ANALYSE / f"{ident}.json"
    if not f.exists():
        analyser_une(ident, PROJETS[ident]["fichier"])
    c = json.loads(f.read_text())["cadre_utile"]
    return c


def cmd_fond(force=False):
    dossier = MEDIA / "accueil"
    if not FOND:
        raise SystemExit("FOND est vide : choisir les plans d'abord.")
    s1080, s720 = dossier / "fond-1080.mp4", dossier / "fond-720.mp4"
    poster = dossier / "fond-poster.jpg"
    if not (force or not s1080.exists() or not s720.exists()):
        print("  fond déjà fait (figé)")
    else:
        dossier.mkdir(parents=True, exist_ok=True)
        # 1) chaque plan : bandes noires retirées puis recadrage centré en 16:9 plein
        #    cadre 1920x1080 (sans déformation)
        entrees, fc = [], []
        for i, (ident, a, b) in enumerate(FOND):
            src = chemin(PROJETS[ident]["fichier"])
            c = cadre_utile(ident)
            entrees += ["-ss", f"{a:.3f}", "-t", f"{b - a:.3f}", "-i", src]
            fc.append(f"[{i}:v]crop={c['w']}:{c['h']}:{c['x']}:{c['y']},"
                      f"scale=1920:1080:force_original_aspect_ratio=increase:flags=lanczos:"
                      f"in_range=tv:out_range=tv:in_color_matrix=bt709:out_color_matrix=bt709,"
                      f"crop=1920:1080,setsar=1,fps=24,format=yuv420p,setpts=PTS-STARTPTS[p{i}]")
        # 2) fondus enchaînés entre plans + retour sur le début du 1er plan pour la boucle
        d = FOND_FONDU
        durees = [b - a for _, a, b in FOND]
        prev, off = "p0", 0.0
        for i in range(1, len(FOND)):
            off += durees[i - 1] - d
            fc.append(f"[{prev}][p{i}]xfade=transition=fade:duration={d}:offset={off:.3f}[x{i}]")
            prev = f"x{i}"
        total = sum(durees) - d * (len(FOND) - 1)
        # boucle : le début du 1er plan (copie) se fond sur la fin, puis on retire
        # ce début de la tête -> la dernière image enchaîne sur la première.
        src0 = chemin(PROJETS[FOND[0][0]]["fichier"])
        c0 = cadre_utile(FOND[0][0])
        entrees += ["-ss", f"{FOND[0][1]:.3f}", "-t", f"{d:.3f}", "-i", src0]
        k = len(FOND)
        fc.append(f"[{k}:v]crop={c0['w']}:{c0['h']}:{c0['x']}:{c0['y']},"
                  f"scale=1920:1080:force_original_aspect_ratio=increase:flags=lanczos:"
                  f"in_range=tv:out_range=tv:in_color_matrix=bt709:out_color_matrix=bt709,"
                  f"crop=1920:1080,setsar=1,fps=24,format=yuv420p,setpts=PTS-STARTPTS[tete]")
        fc.append(f"[{prev}]trim=start={d}:end={total:.3f},setpts=PTS-STARTPTS[corps]")
        fc.append(f"[corps][tete]xfade=transition=fade:duration={d}:"
                  f"offset={total - 2 * d:.3f}[boucle]")
        fc.append("[boucle]split=2[b1][b2]")
        fc.append(f"[b2]{echelle(1280)}[b720]")
        lancer(["ffmpeg", "-nostdin", "-hide_banner", "-v", "error", *entrees,
                "-filter_complex", ";".join(fc),
                "-map", "[b1]", "-an", *x264(*FOND_CRF["1080"], preset="slower"), "-y", s1080,
                "-map", "[b720]", "-an", *x264(*FOND_CRF["720"], preset="slower"), "-y", s720])
        print("  fond-1080.mp4, fond-720.mp4")
    posters_fond(force)


def png_vers_jpeg_cjpeg(png, jpg, qualite):
    """JPEG plus compact (libjpeg-turbo, optimisé, progressif) avec le profil sRGB
    incorporé sans conversion : PNG -> PPM rgb24 (mêmes valeurs) -> cjpeg -icc."""
    ppm = png.with_suffix(".ppm")
    lancer(["ffmpeg", "-nostdin", "-hide_banner", "-v", "error", "-i", png,
            "-pix_fmt", "rgb24", "-y", ppm])
    lancer(["cjpeg", "-quality", str(qualite), "-optimize", "-progressive",
            "-icc", SRGB, "-outfile", jpg, ppm])
    ppm.unlink()


def posters_fond(force=False):
    """Posters du fond : première image de la boucle (1er plan à entrée + fondu),
    prise dans la source avec le même recadrage que la vidéo de fond."""
    dossier = MEDIA / "accueil"
    ident0, a0, _ = FOND[0]
    c0 = cadre_utile(ident0)
    PNG.mkdir(parents=True, exist_ok=True)
    for nom, (larg, haut, qualite) in FOND_POSTERS.items():
        jpg = dossier / nom
        if not a_faire(jpg, force):
            continue
        png = PNG / f"accueil-{jpg.stem}.png"
        lancer(["ffmpeg", "-nostdin", "-hide_banner", "-v", "error",
                "-ss", f"{a0 + FOND_FONDU:.3f}", "-i", chemin(PROJETS[ident0]["fichier"]),
                "-frames:v", "1", "-vf",
                f"crop={c0['w']}:{c0['h']}:{c0['x']}:{c0['y']},"
                f"scale={larg}:{haut}:force_original_aspect_ratio=increase:flags=lanczos:"
                f"in_range=tv:in_color_matrix=bt709,crop={larg}:{haut}",
                "-pix_fmt", "rgb24", "-y", png])
        png_vers_jpeg_cjpeg(png, jpg, qualite)
        print(" ", nom)


def cmd_images(force=False):
    for n, (ident, t) in enumerate(APROPOS, 1):
        src = chemin(PROJETS[ident]["fichier"])
        c = cadre_utile(ident)
        image(src, t, MEDIA / f"apropos-{n}.jpg", min(1400, c["w"]), crop=c, force=force)
    # og.jpg : 1200x630 (1,905:1), recadrage centré du cadre utile
    ident, t = OG
    og = MEDIA / "og.jpg"
    if a_faire(og, force):
        src = chemin(PROJETS[ident]["fichier"])
        c = cadre_utile(ident)
        png = PNG / "og.png"
        PNG.mkdir(parents=True, exist_ok=True)
        vf = (f"crop={c['w']}:{c['h']}:{c['x']}:{c['y']},"
              f"scale=1200:630:force_original_aspect_ratio=increase:flags=lanczos:"
              f"in_range=tv:in_color_matrix=bt709,crop=1200:630")
        lancer(["ffmpeg", "-nostdin", "-hide_banner", "-v", "error", "-ss", f"{t:.3f}",
                "-i", src, "-frames:v", "1", "-vf", vf, "-pix_fmt", "rgb24", "-y", png])
        png_vers_jpeg(png, og)
        print("  og.jpg")


# ---------------------------------------------------------------------------
# 6. VÉRIFICATION + MANIFESTE travail/medias-projets.json
# ---------------------------------------------------------------------------

def faststart(fichier):
    """True si l'atome moov est avant mdat."""
    with open(fichier, "rb") as f:
        pos = 0
        taille_fichier = os.path.getsize(fichier)
        while pos < taille_fichier:
            f.seek(pos)
            h = f.read(16)
            if len(h) < 8:
                break
            taille = int.from_bytes(h[:4], "big")
            typ = h[4:8].decode("latin-1")
            if taille == 1:
                taille = int.from_bytes(h[8:16], "big")
            if typ == "moov":
                return True
            if typ == "mdat":
                return False
            if taille < 8:
                break
            pos += taille
    return False


def controle_video(f):
    s = resume_sonde(f)
    ok = (s["codec"] == "h264" and s["profil"] == "High" and s["pix_fmt"] == "yuv420p"
          and s["primaries"] == s["trc"] == s["matrice"] == "bt709" and s["plage"] == "tv"
          and faststart(f) and s["octets"] < 95 * 1024 * 1024)
    return s, ok


def taille_jpeg(f):
    out = lancer(["sips", "-g", "pixelWidth", "-g", "pixelHeight", "-g", "profile", f],
                 sortie_texte=True)
    d = {}
    for ligne in out.splitlines()[1:]:
        if ":" in ligne:
            k, v = ligne.split(":", 1)
            d[k.strip()] = v.strip()
    return int(d.get("pixelWidth", 0)), int(d.get("pixelHeight", 0)), d.get("profile")


def ecart_png_jpeg(png, jpg):
    """Écart moyen et max des valeurs RVB entre le PNG et le JPEG (décodés par ffmpeg)."""
    def brut(f):
        return subprocess.run(["ffmpeg", "-v", "error", "-i", str(f), "-f", "rawvideo",
                               "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    a, b = brut(png), brut(jpg)
    if len(a) != len(b) or not a:
        return None
    n = len(a)
    pas = max(1, n // 600000)
    diffs = [abs(a[i] - b[i]) for i in range(0, n, pas)]
    moy = [sum(a[i] for i in range(c, n, 3 * pas)) / (n / (3 * pas)) for c in range(3)]
    moy2 = [sum(b[i] for i in range(c, n, 3 * pas)) / (n / (3 * pas)) for c in range(3)]
    return {"ecart_moyen": round(sum(diffs) / len(diffs), 2), "ecart_max": max(diffs),
            "moyennes_rvb_png": [round(x, 1) for x in moy],
            "moyennes_rvb_jpeg": [round(x, 1) for x in moy2]}


def rel_site(f):
    return str(f.relative_to(RACINE / "site"))


def cmd_verifier():
    manif = {"genere_le": time.strftime("%Y-%m-%d %H:%M"), "projets": [], "doublons_ecartes": [],
             "fond": None, "apropos": [], "og": None, "controles": {}}
    problemes = []
    analyse = {}
    # arguments du classement : fichier de travail facultatif, repris dans le manifeste
    fc_ = TRAVAIL / "medias-projets-classement.json"
    arguments = json.loads(fc_.read_text()) if fc_.exists() else {}
    fa = TRAVAIL / "medias-projets-analyse.json"
    if fa.exists():
        analyse = json.loads(fa.read_text())["sources"]

    def fiche_video(f):
        s, ok = controle_video(f)
        if not ok:
            problemes.append(f"contrôle KO : {rel_site(f)} {s}")
        return {"chemin": rel_site(f), "duree": s["duree"], "octets": s["octets"],
                "largeur": s["largeur"], "hauteur": s["hauteur"], "controle_ok": ok}

    def fiche_image(f):
        w, h, prof = taille_jpeg(f)
        if not prof or "sRGB" not in prof:
            problemes.append(f"profil sRGB absent : {rel_site(f)}")
        return {"chemin": rel_site(f), "octets": f.stat().st_size, "largeur": w, "hauteur": h,
                "profil": prof}

    for ident in ORDRE:
        if ident in DOUBLONS:
            continue
        p, m = PROJETS[ident], MOMENTS[ident]
        d = MEDIA / "projets" / ident
        a = analyse.get(ident, {})
        src = a.get("sonde") or resume_sonde(chemin(p["fichier"]))
        fiche = {
            "id": ident, "titre": p["titre"], "fichier_source": p["fichier"],
            "source": {"duree": src["duree"], "octets": src["octets"],
                       "largeur": src["largeur"], "hauteur": src["hauteur"]},
            "ratio_image_utile": (a.get("cadre_utile") or {}).get("ratio"),
            "cadre_utile": a.get("cadre_utile"),
            "ordre": ORDRE.index(ident) + 1,
            "argument_classement": arguments.get(ident),
            "matiere_commune": MATIERE_COMMUNE.get(ident),
            "passages": {"extrait": m["extrait"] or [[0, src["duree"]]],
                         "apercu": m["apercu"], "poster": m["poster"],
                         "miniature": m["miniature"]},
            "fichiers": {},
        }
        for nom in ("apercu", "extrait", "integrale"):
            f = d / f"{nom}.mp4"
            if f.exists():
                fiche["fichiers"][nom] = fiche_video(f)
        for nom in ("poster", "miniature"):
            f = d / f"{nom}.jpg"
            if f.exists():
                fiche["fichiers"][nom] = fiche_image(f)
        fiche["integrale"] = "integrale" in fiche["fichiers"]
        ex = d / "extrait.mp4"
        fiche["son"] = bool(ex.exists() and any(
            st["codec_type"] == "audio" for st in sonder(ex)["streams"]))
        # contrôles de durée et de poids propres à chaque fichier
        f = fiche["fichiers"]
        if "apercu" in f and not (5.9 <= f["apercu"]["duree"] <= 10.1
                                  and f["apercu"]["octets"] < 5 * 1024 * 1024):
            problemes.append(f"{ident} : aperçu hors limites {f['apercu']}")
        if "extrait" in f and src["duree"] > 30.5 and not (19.9 <= f["extrait"]["duree"] <= 30.1):
            problemes.append(f"{ident} : extrait hors 20-30 s {f['extrait']['duree']}")
        if (src["duree"] > 30.5) != fiche["integrale"]:
            problemes.append(f"{ident} : intégrale attendue={src['duree'] > 30.5}")
        manif["projets"].append(fiche)
    manif["doublons_analyse"] = {
        "verdict": "aucun doublon de montage : 8 projets, une carte par vidéo",
        "timeline-1 / timeline-1w": "0 % d'images retrouvées dans les deux sens (image entière et carré central)",
        "wiss-hyrox / wissem-2": "0 % d'images retrouvées dans les deux sens (image entière et carré central)",
        "temoin maroc / maroc-log": "100 % retrouvées (la méthode reconnaît un même montage étalonné autrement)",
        "matiere_commune": MATIERE_COMMUNE,
        "detail": "travail/medias-projets-analyse.json et travail/medias-projets.md",
    }
    for ident, raison in DOUBLONS.items():
        manif["doublons_ecartes"].append({"id": ident, "fichier": PROJETS[ident]["fichier"],
                                          "raison": raison})
    acc = MEDIA / "accueil"
    if (acc / "fond-1080.mp4").exists():
        manif["fond"] = {
            "plans": [{"id": i, "entree": a, "sortie": b} for i, a, b in FOND],
            "fondu_enchaine_s": FOND_FONDU,
            "recadrage": "bandes noires retirées, recadrage centré en 16:9 plein cadre",
            "fond_1080": fiche_video(acc / "fond-1080.mp4"),
            "fond_720": fiche_video(acc / "fond-720.mp4"),
            "poster": fiche_image(acc / "fond-poster.jpg") if (acc / "fond-poster.jpg").exists() else None,
            "poster_720": (fiche_image(acc / "fond-poster-720.jpg")
                           if (acc / "fond-poster-720.jpg").exists() else None),
        }
    if manif["fond"]:
        for k in ("fond_1080", "fond_720"):
            v = manif["fond"][k]
            if not (12 <= v["duree"] <= 20):
                problemes.append(f"{k} : durée {v['duree']} hors 12-20 s")
            if v["octets"] > 8 * 1024 * 1024:
                problemes.append(f"{k} : {v['octets']} octets > 8 Mo")
    for n, (ident, t) in enumerate(APROPOS, 1):
        f = MEDIA / f"apropos-{n}.jpg"
        if f.exists():
            manif["apropos"].append({**fiche_image(f), "id": ident, "instant": t})
    if (MEDIA / "og.jpg").exists():
        manif["og"] = {**fiche_image(MEDIA / "og.jpg"), "id": OG[0], "instant": OG[1]}
    # contrôle couleur : PNG vs JPEG sur quelques images
    ech = {}
    for png, jpg in [(PNG / "disney-poster.png", MEDIA / "projets/disney/poster.jpg"),
                     (PNG / "maroc-poster.png", MEDIA / "projets/maroc/poster.jpg"),
                     (PNG / "og.png", MEDIA / "og.jpg"),
                     (PNG / "accueil-fond-poster.png", MEDIA / "accueil/fond-poster.jpg"),
                     (PNG / "accueil-fond-poster-720.png", MEDIA / "accueil/fond-poster-720.jpg")]:
        if png.exists() and jpg.exists():
            ech[rel_site(jpg)] = ecart_png_jpeg(png, jpg)
    manif["controles"]["png_vs_jpeg"] = ech
    # poids des dossiers
    def poids(dossier):
        return sum(f.stat().st_size for f in dossier.rglob("*") if f.is_file())
    manif["controles"]["poids_site_media_octets"] = poids(MEDIA) if MEDIA.exists() else 0
    manif["controles"]["poids_medias_projets_octets"] = (
        sum(poids(MEDIA / "projets" / i) for i in PROJETS if (MEDIA / "projets" / i).exists())
        + (poids(acc) if acc.exists() else 0)
        + sum((MEDIA / n).stat().st_size for n in ("apropos-1.jpg", "apropos-2.jpg", "og.jpg")
              if (MEDIA / n).exists()))
    manif["controles"]["poids_integrales_octets"] = sum(
        (MEDIA / "projets" / i / "integrale.mp4").stat().st_size for i in PROJETS
        if (MEDIA / "projets" / i / "integrale.mp4").exists())
    manif["controles"]["problemes"] = problemes
    (TRAVAIL / "medias-projets.json").write_text(json.dumps(manif, ensure_ascii=False, indent=1))
    print("manifeste : travail/medias-projets.json")
    print("problèmes :", problemes or "aucun")
    print("poids site/media :", manif["controles"]["poids_site_media_octets"])
    print("png vs jpeg :", json.dumps(ech, ensure_ascii=False))


# ---------------------------------------------------------------------------

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    force = "--force" in sys.argv
    if not args:
        print(__doc__)
        return
    cmd, reste = args[0], args[1:]
    if cmd == "analyse":
        cmd_analyse(force)
    elif cmd == "planches":
        cmd_planches(force=force)
    elif cmd == "projets":
        cmd_projets(reste or None, force)
    elif cmd == "fond":
        cmd_fond(force)
    elif cmd == "posters-fond":
        posters_fond(force)
    elif cmd == "images":
        cmd_images(force)
    elif cmd == "verifier":
        cmd_verifier()
    elif cmd == "tout":
        cmd_analyse()
        cmd_projets(None, force)
        cmd_fond(force)
        cmd_images(force)
        cmd_verifier()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
