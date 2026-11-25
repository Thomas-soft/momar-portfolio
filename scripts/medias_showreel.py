#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
medias_showreel.py : le showreel du portfolio de Momar Gaye (57 s, 1920x1080, 16:9 plein cadre).

À lancer depuis n'importe où (les chemins partent du dossier du projet) :

  python3 -I scripts/medias_showreel.py plans       # affiche le montage (entrées, durées, place sur les temps)
  python3 -I scripts/medias_showreel.py rendu       # site/media/showreel/showreel.mp4 et poster.jpg
  python3 -I scripts/medias_showreel.py controles   # ffprobe, loudness, images noires, bords, planche
  python3 -I scripts/medias_showreel.py tout        # rendu puis contrôles
  Ajouter --force pour refaire un fichier déjà produit (sans --force, rien n'est réencodé).

Pour retoucher le montage : modifier PLANS (en secondes dans la vidéo source), puis relancer
« rendu --force ». Chaque plan doit durer un nombre entier d'images (1/24 s) ; la somme des plans
doit faire la durée de la musique moins le carton final (la commande « plans » le vérifie et
indique où tombe chaque coupe sur les temps de la musique).

Couleur : aucun LUT, aucun filtre, aucune correction. Seulement recadrage et redimensionnement
(lanczos, plage limitée, matrice BT.709), comme scripts/medias_projets.py. Vidéo H.264 High,
yuv420p, faststart, étiquetée BT.709 x3, plage limitée (tv). Poster : JPEG avec le profil sRGB
incorporé sans conversion des valeurs (sips --embedProfile).

Carton final : dessiné avec Pillow (EB Garamond 500, licence OFL) dans travail/showreel/carton.png.
Si l'image existe, Pillow n'est pas nécessaire. Sinon : lancer « carton » avec un Python qui a Pillow.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
TRAVAIL = RACINE / "travail"
TMP = TRAVAIL / "tmp-showreel" / "rendu"
SORTIE = RACINE / "site" / "media" / "showreel"
VIDEO = SORTIE / "showreel.mp4"
POSTER_JPG = SORTIE / "poster.jpg"
CARTON_PNG = TRAVAIL / "showreel" / "carton.png"
PLANCHE = TRAVAIL / "planches" / "showreel.jpg"
JOURNAL = TRAVAIL / "medias-showreel.log"
SRGB = "/System/Library/ColorSync/Profiles/sRGB Profile.icc"

# ---------------------------------------------------------------------------
# 1. DONNÉES DU MONTAGE (à modifier ici, puis relancer « rendu --force »)
# ---------------------------------------------------------------------------

FPS = 24
TEMPS = 0.625      # un temps de la musique (96 BPM) = 15 images ; une mesure = 4 temps = 2,5 s
DROP = 5.0         # premier temps fort (entrée du rythme) dans le showreel, en secondes

# Sources : versions étalonnées uniquement (jamais les versions LOG).
SOURCES = {
    "wiss-hyrox":  "originaux/wetransfer-2/wiss hyrox final 3.mov",
    "timeline-1w": "originaux/wetransfer-2/Timeline 1w.mov",
    "disney":      "originaux/wetransfer-1/disney v1.mov",
    "wissem-2":    "originaux/wetransfer-2/wissem 2.mov",
    "timeline-1":  "originaux/wetransfer-1/Timeline 1.mov",
    "marco":       "originaux/wetransfer-1/marco.mov",
    "maroc":       "originaux/wetransfer-1/vlog maroc grade.mov",
    "training":    "originaux/wetransfer-1/training grade.mov",
}

# Image utile des sources à bandes noires latérales (largeur, hauteur, x, y), mesurée par
# « medias_projets.py analyse ». On y découpe une fenêtre 16:9 pleine largeur, placée en hauteur
# par le recadrage du plan (0 = en haut, 1 = en bas), puis on la met à 1920x1080.
IMAGE_UTILE = {
    "wiss-hyrox":  (2964, 2160, 438, 0),    # 1,372:1 (4K)
    "timeline-1w": (1376, 1080, 272, 0),    # 1,274:1
}
# Wiss Hyrox a des sous-titres incrustés en bas (lignes vers y = 1990-2100 sur 2160) :
# la fenêtre 16:9 doit s'arrêter au-dessus de cette ligne (le script le vérifie).
LIMITE_BASSE = {"wiss-hyrox": 1960}

# Les plans, dans l'ordre : (projet, début, fin, recadrage, ce qu'on voit).
#   début / fin : secondes dans la source (fin - début = nombre entier d'images).
#   recadrage   : None pour une source déjà en 16:9 plein cadre ;
#                 0 à 1 = position verticale de la fenêtre 16:9 dans l'image utile.
# Structure (sur la musique) : accroche 0-5 s | 1er drop 5-25 s | respiration 25-35 s |
# 2e drop 35-55 s | carton 55-57 s.
PLANS = [
    # --- accroche (nappe qui monte puis se retient avant le drop) ---
    ("timeline-1w", 20.333, 22.833, 0.50, "drone à la verticale de la piste rouge, le coureur seul"),
    ("wiss-hyrox",  17.500, 20.000, 0.15, "verrière du Grand Palais, la caméra descend sur le portique START"),
    # --- 1er drop (5 s) : le sport ---
    ("wiss-hyrox",  20.083, 21.000, 0.55, "athlètes alignés sous le portique START"),
    ("wiss-hyrox",  25.250, 26.833, 0.40, "coureurs en contre-plongée sous les arcades"),
    ("wissem-2",     5.542,  6.500, None, "battle ropes sur le gazon"),
    ("timeline-1w", 23.917, 25.458, 0.50, "noir et blanc : le coureur arrive face caméra"),
    ("wiss-hyrox",  21.750, 23.000, 0.55, "rameurs Concept2"),
    ("wissem-2",    15.917, 17.167, None, "visage dans les néons"),
    ("wiss-hyrox",  48.750, 51.250, 0.25, "wall balls sous la verrière, le ballon en l'air"),
    ("timeline-1w", 35.500, 36.750, 0.15, "contre-plongée sur ciel bleu, il boit"),
    ("disney",      74.833, 76.083, None, "Orbitron de Discoveryland"),
    ("wiss-hyrox",  43.750, 45.000, 0.30, "deux athlètes, casquette rouge"),
    ("marco",       86.000, 87.250, None, "harira et tajines, couleurs vives"),
    ("timeline-1w",  6.917,  8.167, 0.50, "noir et blanc : penché, il reprend son souffle"),
    ("timeline-1",  10.000, 11.250, None, "éclat de rire en terrasse"),
    ("wissem-2",    20.792, 22.042, None, "le cri, néon « se dépasser »"),
    ("marco",       32.083, 33.333, None, "le soleil à travers la terrasse"),
    # --- respiration (nappe seule, puis montée et silence avant le 2e drop) ---
    ("disney",      59.500, 62.000, None, "couple au restaurant, contre-jour"),
    ("marco",       40.500, 43.000, None, "coucher de soleil, lanterne"),
    ("marco",      130.000, 132.500, None, "main dans la main sous les palmiers"),
    ("wiss-hyrox",   0.500,  3.000, 0.40, "coulisses : les athlètes s'échauffent"),
    # --- 2e drop (35 s) : la nuit, puis les couleurs, puis l'arrivée ---
    ("marco",       80.750, 82.000, None, "Marrakech la nuit, foule et lumières"),
    ("disney",      92.500, 93.750, None, "enseigne néon Disney"),
    ("training",     1.000,  2.250, None, "Burger King de nuit, lumières chaudes"),
    ("marco",      124.750, 126.000, None, "place Jemaa el-Fna la nuit"),
    ("disney",      67.000, 68.250, None, "Frontierland au crépuscule, Big Thunder Mountain"),
    ("maroc",        1.000,  2.250, None, "la bouteille d'eau vers l'objectif"),
    ("timeline-1w", 13.500, 14.750, 0.40, "coureur en bleu, pins et ciel"),
    ("marco",       66.333, 67.583, None, "tortue dans l'herbe"),
    ("marco",      110.000, 112.500, None, "allée rouge entre les bambous"),
    ("disney",      90.750, 92.000, None, "pâtisserie en gros plan"),
    ("timeline-1",  37.000, 38.250, None, "lunettes de soleil, le geste"),
    ("disney",      95.750, 97.333, None, "devant le château"),
    ("timeline-1w",  2.417,  3.333, 0.50, "noir et blanc : le coureur de dos"),
    ("wiss-hyrox",  84.000, 85.250, 0.50, "l'athlète au sol après la ligne d'arrivée"),
    ("wiss-hyrox",  86.167, 87.417, 0.50, "il se relève et repart devant le mur HYROX"),
]

# Musique (Pixabay, licence Pixabay : usage libre, attribution non requise) :
# « Dark Cinematic Ambient Beat » de rockot, Pixabay n° 173058, 96 BPM.
MUSIQUE = "originaux/musique/rockot-dark-cinematic-ambient-beat-173058.mp3"
# Passages du morceau (secondes dans le MP3) mis bout à bout. Les raccords tombent sur une barre
# de mesure, à la même place de la boucle d'accords (4 mesures), entre passages quasi identiques :
#   17,536-42,536 : fin de l'intro (montée) + drop à 22,536 + 8 mesures de rythme
#   62,536-67,536 : début du pont (le rythme s'arrête comme à la fin naturelle de la section)
#   77,536-92,536 : fin du pont (montée, silence) + 2e drop à 82,536 + 4 mesures
#   112,536-124,536 : 4 dernières mesures de la section + 2 s de nappe (fin, fondu)
MUSIQUE_PASSAGES = [(17.536, 42.536), (62.536, 67.536), (77.536, 92.536), (112.536, 124.536)]
RACCORD = 0.05        # fondu enchaîné de 50 ms juste avant chaque raccord (évite le clic)
FONDU_ENTREE = 0.15
FONDU_SORTIE = 1.5
LUFS = -14.0          # loudness intégrée visée
CRETE_MAX = -1.0      # crête vraie maximale (dBTP)

# Carton final (fond noir, lettres crème du site).
CARTON = {
    "texte": "MOMAR GAYE",
    "duree": 2.0,
    "police": "travail/polices/EBGaramond-500.ttf",   # EB Garamond 500, licence OFL
    "taille": 96,              # pixels (hauteur du corps)
    "interlettre": 0.16,       # espacement ajouté entre les lettres, en fraction du corps
    "couleur": (243, 239, 230),  # #f3efe6
    "fondu_entree": 0.3,
    "fondu_sortie": 0.6,
}

# Poster : (numéro du plan à partir de 1, secondes après le début du plan), image forte et nette.
POSTER = (9, 0.85)   # wall balls sous la verrière du Grand Palais, le ballon en l'air

# Encodage (mêmes réglages que les extraits du site, plafond adapté pour rester < 40 Mo).
CRF, PLAFOND = 20, 5000
AUDIO = ["-c:a", "aac", "-b:a", "192k", "-ac", "2", "-ar", "48000"]
COULEUR = ["-color_primaries", "bt709", "-color_trc", "bt709",
           "-colorspace", "bt709", "-color_range", "tv"]
ECHELLE = ("scale=1920:1080:flags=lanczos:in_range=tv:out_range=tv:"
           "in_color_matrix=bt709:out_color_matrix=bt709")

# ---------------------------------------------------------------------------
# 2. OUTILS
# ---------------------------------------------------------------------------


def journal(msg):
    TRAVAIL.mkdir(exist_ok=True)
    with open(JOURNAL, "a", encoding="utf-8") as f:
        f.write(time.strftime("%H:%M:%S ") + msg + "\n")


def lancer(cmd, texte=False):
    journal("$ " + " ".join(str(c) for c in cmd))
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if r.returncode != 0:
        journal(r.stderr[-6000:])
        raise SystemExit(f"Échec : {cmd[0]} (voir {JOURNAL})")
    return (r.stdout, r.stderr) if texte else None


def a_faire(f, force):
    if f.exists() and not force:
        print("  déjà fait (figé) :", f.relative_to(RACINE))
        return False
    f.parent.mkdir(parents=True, exist_ok=True)
    return True


def nb_images(debut, fin):
    n = round((fin - debut) * FPS)
    if abs(n / FPS - (fin - debut)) > 0.01:
        raise SystemExit(f"Plan {debut}-{fin} : la durée n'est pas un nombre entier d'images.")
    return n


def fenetre(projet, pos):
    """Recadrage 16:9 (w, h, x, y) dans l'image utile, ou None (source déjà 16:9)."""
    if projet not in IMAGE_UTILE:
        if pos is not None:
            raise SystemExit(f"{projet} : source 16:9, le recadrage doit être None.")
        return None
    if pos is None or not 0 <= pos <= 1:
        raise SystemExit(f"{projet} : recadrage attendu entre 0 et 1.")
    w, h, x, y = IMAGE_UTILE[projet]
    fh = round(w * 9 / 16 / 2) * 2
    fy = y + int(round((h - fh) * pos / 2)) * 2
    if fy + fh > LIMITE_BASSE.get(projet, 10 ** 6):
        raise SystemExit(f"{projet} : recadrage {pos} trop bas (sous-titres dans l'image).")
    return (w, fh, x, fy)


def filtre_image(projet, pos):
    c = fenetre(projet, pos)
    crop = f"crop={c[0]}:{c[1]}:{c[2]}:{c[3]}," if c else ""
    return crop + ECHELLE + ",setsar=1"


def duree_musique():
    return sum(b - a for a, b in MUSIQUE_PASSAGES)


def montage():
    """[(n°, projet, début, fin, recadrage, quoi, entrée dans le showreel, nb d'images)]"""
    out, t = [], 0
    for i, (projet, a, b, pos, quoi) in enumerate(PLANS, 1):
        if projet not in SOURCES:
            raise SystemExit(f"Projet inconnu : {projet}")
        n = nb_images(a, b)
        if not 0.8 <= n / FPS <= 3.0:
            print(f"  attention : plan {i} de {n / FPS:.2f} s (hors 0,8-3 s)")
        fenetre(projet, pos)
        out.append((i, projet, a, b, pos, quoi, t, n))
        t += n
    total = t + round(CARTON["duree"] * FPS)
    if abs(total / FPS - duree_musique()) > 1e-6:
        raise SystemExit(f"Plans + carton = {total / FPS:.3f} s, musique = {duree_musique():.3f} s : "
                         "ajuster les plans.")
    return out


def cmd_plans():
    print(f"{'n°':>3} {'entrée':>7} {'durée':>6} {'temps':>6}  projet       source            quoi")
    for i, projet, a, b, pos, quoi, t, n in montage():
        tps = (t / FPS - DROP) / TEMPS
        place = f"{tps:+.1f}" if abs(tps * 2 - round(tps * 2)) < 0.1 else f"{tps:+.2f}!"
        print(f"{i:>3} {t / FPS:7.3f} {n / FPS:6.3f} {place:>6}  {projet:<12} "
              f"{a:7.3f}-{b:7.3f}  {quoi}")
    fin = sum(n for *_, n in montage()) / FPS
    print(f"carton {fin:.3f} -> {fin + CARTON['duree']:.3f} s ; musique {duree_musique():.3f} s")


# ---------------------------------------------------------------------------
# 3. CARTON, MUSIQUE, VIDÉO, POSTER
# ---------------------------------------------------------------------------

def cmd_carton(force=False):
    if not a_faire(CARTON_PNG, force):
        return
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        raise SystemExit("Pillow manque : lancer « carton » avec un Python qui a Pillow "
                         "(python3 -m pip install pillow), ou garder travail/showreel/carton.png.")
    k = 4   # dessin 4x plus grand puis réduction : bords de lettres lisses
    grande = ImageFont.truetype(str(RACINE / CARTON["police"]), CARTON["taille"] * k)
    texte, esp = CARTON["texte"], CARTON["interlettre"] * CARTON["taille"] * k
    largeurs = [grande.getlength(ch) for ch in texte]
    total = sum(largeurs) + esp * (len(texte) - 1)
    img = Image.new("L", (1920 * k, 1080 * k), 0)
    d = ImageDraw.Draw(img)
    bas = grande.getbbox(texte)   # centrage vertical sur la hauteur réelle des lettres
    y = (1080 * k - (bas[3] - bas[1])) / 2 - bas[1]
    x = (1920 * k - total) / 2
    for ch, lw in zip(texte, largeurs):
        d.text((x, y), ch, font=grande, fill=255)
        x += lw + esp
    masque = img.resize((1920, 1080), Image.LANCZOS)
    rvb = Image.new("RGB", (1920, 1080), (0, 0, 0))
    rvb.paste(Image.new("RGB", (1920, 1080), CARTON["couleur"]), (0, 0), masque)
    rvb.save(CARTON_PNG)
    print("  carton", CARTON_PNG.relative_to(RACINE))


def musique_wav():
    """Assemble les passages (fondus enchaînés de RACCORD avant chaque raccord), fondus
    d'entrée et de sortie, 48 kHz stéréo, en WAV 32 bits flottants."""
    TMP.mkdir(parents=True, exist_ok=True)
    wav = TMP / "musique.wav"
    k = len(MUSIQUE_PASSAGES)
    fc = [f"[0:a]asplit={k}" + "".join(f"[s{j}]" for j in range(k))]
    for j, (a, b) in enumerate(MUSIQUE_PASSAGES):
        a0 = a - (RACCORD if j else 0)
        fc.append(f"[s{j}]atrim=start={a0:.4f}:end={b:.4f},asetpts=PTS-STARTPTS[p{j}]")
    prec = "p0"
    for j in range(1, k):
        fc.append(f"[{prec}][p{j}]acrossfade=d={RACCORD}:c1=tri:c2=tri[x{j}]")
        prec = f"x{j}"
    total = duree_musique()
    fc.append(f"[{prec}]aresample=48000,afade=t=in:st=0:d={FONDU_ENTREE},"
              f"afade=t=out:st={total - FONDU_SORTIE:.4f}:d={FONDU_SORTIE},"
              f"atrim=end={total:.4f}[m]")
    lancer(["ffmpeg", "-nostdin", "-hide_banner", "-v", "error", "-i", RACINE / MUSIQUE,
            "-filter_complex", ";".join(fc), "-map", "[m]", "-c:a", "pcm_f32le",
            "-ac", "2", "-y", wav])
    return wav


def loudness(fichier):
    """(loudness intégrée LUFS, crête vraie dBTP) mesurées par ebur128."""
    _, err = lancer(["ffmpeg", "-nostdin", "-hide_banner", "-nostats", "-i", fichier, "-map", "0:a:0",
                     "-af", "ebur128=peak=true", "-f", "null", "-"], texte=True)
    resume = err[err.rfind("Summary:"):]
    i = float(re.search(r"I:\s+(-?[\d.]+) LUFS", resume).group(1))
    tp = float(re.search(r"Peak:\s+(-?[\d.]+|-inf) dBFS", resume).group(1))
    lra = float(re.search(r"LRA:\s+(-?[\d.]+) LU", resume).group(1))
    return i, tp, lra


def chaine_son(wav):
    """Gain pour viser LUFS ; limiteur doux seulement si la crête vraie dépasserait CRETE_MAX."""
    i, tp, _ = loudness(wav)
    gain = LUFS - i
    filtre = f"volume={gain:.2f}dB"
    if tp + gain > CRETE_MAX:
        lim = 10 ** ((CRETE_MAX - 0.5) / 20)
        filtre += f",alimiter=limit={lim:.4f}:attack=5:release=60:level=disabled"
    print(f"  musique assemblée : {i:.1f} LUFS, crête {tp:.1f} dBTP -> gain {gain:+.1f} dB")
    return filtre


def cmd_rendu(force=False):
    plans = montage()
    if a_faire(VIDEO, force):
        if not CARTON_PNG.exists():
            cmd_carton()
        wav = musique_wav()
        son = chaine_son(wav)
        entrees, fc = [], []
        for k, (i, projet, a, b, pos, quoi, t, n) in enumerate(plans):
            entrees += ["-ss", f"{a:.3f}", "-t", f"{n / FPS + 0.5:.3f}", "-i", RACINE / SOURCES[projet]]
            fc.append(f"[{k}:v]trim=end_frame={n},setpts=PTS-STARTPTS,{filtre_image(projet, pos)},"
                      f"fps={FPS},format=yuv420p[v{k}]")
        kc = len(plans)
        dc = CARTON["duree"]
        entrees += ["-loop", "1", "-framerate", str(FPS), "-t", f"{dc:.3f}", "-i", CARTON_PNG]
        fc.append(f"[{kc}:v]scale=1920:1080:in_range=pc:out_range=tv:out_color_matrix=bt709,"
                  f"setsar=1,fps={FPS},format=yuv420p,"
                  f"fade=t=in:st=0:d={CARTON['fondu_entree']},"
                  f"fade=t=out:st={dc - CARTON['fondu_sortie']:.3f}:d={CARTON['fondu_sortie']},"
                  f"trim=end_frame={round(dc * FPS)}[v{kc}]")
        fc.append("".join(f"[v{k}]" for k in range(kc + 1)) + f"concat=n={kc + 1}:v=1:a=0[v]")
        ka = kc + 1
        entrees += ["-i", wav]
        fc.append(f"[{ka}:a]{son}[a]")
        tmp = VIDEO.with_suffix(".tmp.mp4")
        lancer(["ffmpeg", "-nostdin", "-hide_banner", "-v", "error", *entrees,
                "-filter_complex", ";".join(fc), "-map", "[v]", "-map", "[a]",
                "-c:v", "libx264", "-preset", "slow", "-profile:v", "high", "-pix_fmt", "yuv420p",
                "-crf", str(CRF), "-maxrate", f"{PLAFOND}k", "-bufsize", f"{2 * PLAFOND}k",
                "-g", "48", "-x264-params", "aq-mode=3", *AUDIO, "-movflags", "+faststart",
                "-map_metadata", "-1", "-map_chapters", "-1", *COULEUR, "-y", tmp])
        tmp.replace(VIDEO)
        print("  vidéo", VIDEO.relative_to(RACINE), f"{VIDEO.stat().st_size / 1e6:.1f} Mo")
    cmd_poster(force)
    shutil.rmtree(TMP, ignore_errors=True)


def cmd_poster(force=False):
    if not a_faire(POSTER_JPG, force):
        return
    i, dt = POSTER
    projet, a, b, pos, _ = PLANS[i - 1]
    TMP.mkdir(parents=True, exist_ok=True)
    png = TMP / "poster.png"
    c = fenetre(projet, pos)
    vf = (f"crop={c[0]}:{c[1]}:{c[2]}:{c[3]}," if c else "") + \
        "scale=1920:1080:flags=lanczos:in_range=tv:in_color_matrix=bt709"
    lancer(["ffmpeg", "-nostdin", "-hide_banner", "-v", "error", "-ss", f"{a + dt:.3f}",
            "-i", RACINE / SOURCES[projet], "-frames:v", "1", "-vf", vf, "-pix_fmt", "rgb24", "-y", png])
    # un seul appel : JPEG + profil sRGB incorporé, sans conversion des valeurs
    lancer(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "90",
            "--embedProfile", SRGB, png, "--out", POSTER_JPG])
    print("  poster", POSTER_JPG.relative_to(RACINE))


# ---------------------------------------------------------------------------
# 4. CONTRÔLES
# ---------------------------------------------------------------------------

def faststart(fichier):
    with open(fichier, "rb") as f:
        pos, taille_f = 0, os.path.getsize(fichier)
        while pos < taille_f:
            f.seek(pos)
            h = f.read(16)
            if len(h) < 8:
                break
            taille, typ = int.from_bytes(h[:4], "big"), h[4:8].decode("latin-1")
            if taille == 1:
                taille = int.from_bytes(h[8:16], "big")
            if typ in ("moov", "mdat"):
                return typ == "moov"
            if taille < 8:
                break
            pos += taille
    return False


def cmd_controles():
    if not VIDEO.exists():
        raise SystemExit("Pas de vidéo : lancer « rendu » d'abord.")
    res, problemes = {}, []
    out, _ = lancer(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", VIDEO],
                    texte=True)
    p = json.loads(out)
    v = next(s for s in p["streams"] if s["codec_type"] == "video")
    a = next(s for s in p["streams"] if s["codec_type"] == "audio")
    res["ffprobe"] = {
        "duree": round(float(p["format"]["duration"]), 3), "octets": int(p["format"]["size"]),
        "video": f"{v['codec_name']} {v.get('profile')} {v['width']}x{v['height']} {v['pix_fmt']} "
                 f"{v.get('r_frame_rate')} images {v.get('nb_frames')} SAR {v.get('sample_aspect_ratio')}",
        "couleur": f"{v.get('color_primaries')}/{v.get('color_transfer')}/{v.get('color_space')} "
                   f"plage {v.get('color_range')}",
        "debit_video_kbs": round(int(v.get("bit_rate", 0)) / 1000),
        "audio": f"{a['codec_name']} {a.get('profile')} {a['sample_rate']} Hz {a['channels']} canaux "
                 f"{round(int(a.get('bit_rate', 0)) / 1000)} kb/s",
        "faststart": faststart(VIDEO),
    }
    if not (v["codec_name"] == "h264" and v.get("profile") == "High" and v["pix_fmt"] == "yuv420p"
            and v["width"] == 1920 and v["height"] == 1080
            and v.get("color_primaries") == v.get("color_transfer") == v.get("color_space") == "bt709"
            and v.get("color_range") == "tv" and res["ffprobe"]["faststart"]):
        problemes.append("format vidéo")
    if res["ffprobe"]["octets"] > 40 * 1024 * 1024:
        problemes.append("poids > 40 Mo")
    i, tp, lra = loudness(VIDEO)
    res["loudness"] = {"integree_lufs": i, "crete_vraie_dbtp": tp, "lra_lu": lra}
    if not -16.5 <= i <= -13.5 or tp > CRETE_MAX + 0.2:
        problemes.append("loudness")
    # images noires (seuil : 98 % des pixels sous 10 % de la plage)
    _, err = lancer(["ffmpeg", "-nostdin", "-hide_banner", "-i", VIDEO, "-map", "0:v:0",
                     "-vf", "blackdetect=d=0.04:pix_th=0.10:pic_th=0.98", "-f", "null", "-"], texte=True)
    noirs = [(float(m.group(1)), float(m.group(2))) for m in
             re.finditer(r"black_start:([\d.]+) black_end:([\d.]+)", err)]
    debut_carton = sum(n for *_, n in montage()) / FPS
    res["images_noires"] = noirs
    hors = [x for x in noirs if x[1] <= debut_carton + 0.01 or x[0] < debut_carton - 0.01]
    if hors:
        problemes.append(f"images noires hors carton : {hors}")
    # bords : une bande noire résiduelle se verrait en colonnes/lignes de bord très sombres
    _, err = lancer(["ffmpeg", "-nostdin", "-hide_banner", "-t", f"{debut_carton:.3f}", "-i", VIDEO,
                     "-vf", "fps=4,cropdetect=limit=12:round=2:reset=1:mode=black", "-f", "null", "-"],
                    texte=True)
    crops = {}
    for m in re.finditer(r"t:([\d.]+) .*crop=(\d+:\d+:\d+:\d+)", err):
        crops.setdefault(m.group(2), []).append(round(float(m.group(1)), 2))
    res["bords_cropdetect"] = {k: (len(t), t[:6]) for k, t in crops.items()}
    # planche : une image toutes les 0,75 s (au milieu de chaque tranche)
    planche()
    res["problemes"] = problemes
    print(json.dumps(res, ensure_ascii=False, indent=1))
    (TRAVAIL / "showreel-controles.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
    return res


def planche(pas=0.75, cols=8, larg=236):
    PLANCHE.parent.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    out, _ = lancer(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                     VIDEO], texte=True)
    duree = float(out)
    n = int(duree / pas)
    # images exactes : n° (pas/2 + k*pas) x FPS (0,375 s, 1,125 s, ...), sans arrondi du filtre fps
    premier, ecart = round(pas / 2 * FPS), round(pas * FPS)
    images = TMP / "planche-%03d.png"
    lancer(["ffmpeg", "-nostdin", "-hide_banner", "-v", "error", "-i", VIDEO,
            "-vf", f"select='gte(n\\,{premier})*not(mod(n-{premier}\\,{ecart}))',"
                   f"scale={larg}:-2:in_range=tv:in_color_matrix=bt709",
            "-fps_mode", "vfr", "-frames:v", str(n), "-pix_fmt", "rgb24", "-y", images])
    fichiers = sorted(TMP.glob("planche-*.png"))
    try:
        from PIL import Image, ImageDraw, ImageFont
        ims = [Image.open(f).convert("RGB") for f in fichiers]
        w, h = ims[0].size
        lignes = (len(ims) + cols - 1) // cols
        feuille = Image.new("RGB", (cols * (w + 4), lignes * (h + 22)), (40, 40, 40))
        d = ImageDraw.Draw(feuille)
        try:
            police = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 14)
        except OSError:
            police = ImageFont.load_default()
        for k, im in enumerate(ims):
            x, y = (k % cols) * (w + 4), (k // cols) * (h + 22)
            feuille.paste(im, (x, y))
            d.text((x + 3, y + h + 2), f"{pas / 2 + k * pas:.2f} s", fill=(255, 230, 0), font=police)
        feuille.save(PLANCHE, quality=88)
    except ImportError:
        # sans Pillow : planche sans étiquettes (image k à (k + 0,5) x pas secondes)
        lancer(["ffmpeg", "-nostdin", "-hide_banner", "-v", "error", "-i", TMP / "planche-%03d.png",
                "-vf", f"tile={cols}x{(len(fichiers) + cols - 1) // cols}:padding=4:color=0x282828",
                "-frames:v", "1", "-q:v", "3", "-y", PLANCHE])
    for f in fichiers:
        f.unlink()
    print("  planche", PLANCHE.relative_to(RACINE), f"({len(fichiers)} images, une toutes les {pas} s)")


# ---------------------------------------------------------------------------

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    force = "--force" in sys.argv
    cmd = args[0] if args else "plans"
    if cmd == "plans":
        cmd_plans()
    elif cmd == "carton":
        cmd_carton(force)
    elif cmd == "rendu":
        cmd_rendu(force)
    elif cmd == "poster":
        cmd_poster(force)
    elif cmd == "controles":
        cmd_controles()
    elif cmd == "tout":
        cmd_rendu(force)
        cmd_controles()
    else:
        raise SystemExit(__doc__)
    # fichiers intermédiaires : supprimés à chaque fin de commande
    shutil.rmtree(TMP, ignore_errors=True)
    try:
        TMP.parent.rmdir()   # travail/tmp-showreel, seulement s'il est vide
    except OSError:
        pass


if __name__ == "__main__":
    main()
