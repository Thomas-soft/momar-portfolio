#!/usr/bin/env python3
"""Médias d'étalonnage du portfolio de Momar : Maroc et Training (LOG / GRADED).

Produit, à partir des originaux (jamais modifiés) :
  site/media/comparateurs/<id>-<n>-log.jpg et <id>-<n>-graded.jpg   (1920x1080)
  site/media/comparateurs/<id>-video.mp4 et <id>-video-poster.jpg   (1280x1456 : LOG en haut, bande noire 16 px, GRADED en bas)
  site/media/galerie/<id>-<n>.jpg                                    (1920x1080, GRADED)
  travail/medias-etalonnage.json                                     (manifeste)
Fichiers de travail : travail/etalonnage/ (PNG, analyses), travail/planches/etal-*.jpg, travail/medias-etalonnage-*.log

Usage :  python3 -I scripts/medias_etalonnage.py [--force] [etape ...]
  étapes : analyse planches images videos verif manifeste   (par défaut : toutes, dans cet ordre)
  Sans --force, un média déjà produit n'est jamais réencodé (médias figés) et l'analyse en cache est relue.
Dépendances : python3 (bibliothèque standard seulement), ffmpeg, ffprobe, sips (macOS).
Couleur : aucun LUT, aucun filtre, aucune correction. Les images LOG restent telles quelles.
"""
import json
import math
import os
import subprocess
import sys
import time

# =====================================================================================
# DONNÉES (choix faits à partir des planches travail/planches/etal-*.jpg et de l'analyse)
# Numéros d'image = index 0-based dans la source (24 images/s, temps = n / 24).
# decalage : image LOG = image GRADED + decalage (mesuré par l'étape « analyse »).
# =====================================================================================
RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS = 24

PROJETS = {
    "maroc": {
        "graded": "originaux/wetransfer-1/vlog maroc grade.mov",
        "log": "originaux/wetransfer-1/vlog maroc log .mov",   # une espace avant .mov
        "decalage": 0,          # mesuré : 0 image ; la 481e image du LOG (n° 480) est noire, en fin de fichier
        "derniere_image": 479,  # dernière image commune utile (GRADED 0..479, LOG 0..479, LOG 480 = noire)
        # plans : [début, fin] inclus, identiques dans les deux versions
        "plans": [[0, 136], [137, 479]],
        "plans_exclus": [],     # plans où LOG et GRADED ne montrent pas la même image
        # comparateurs d'images : numéro d'image GRADED (et LOG si différent, sinon LOG = GRADED + decalage)
        "comparateurs": [
            {"graded": 150},   # 1 : jardin, plan large fixe (avant le carton « The end », qui apparaît à l'image 187)
            {"graded": 12},    # 2 : intérieur, visage face caméra
            {"graded": 46},    # 3 : intérieur, la bouteille versée à l'horizontale
            {"graded": 108},   # 4 : intérieur, bras levé, bouteille inclinée
        ],
        # comparateur vidéo : segments GRADED [début, fin] inclus, mis bout à bout
        # Le carton « The end » apparaît d'un coup à l'image 187 (dans les deux versions) et reste jusqu'à la fin :
        # tout ce qui précède tient en 7,79 s, on ne peut pas atteindre 8 s sans lui.
        "carton": 187,
        "video": [[0, 186]],   # 7,79 s : plan intérieur entier puis 2,1 s du jardin, sans le carton
        "galerie": [84, 119],  # images GRADED
    },
    "training": {
        "graded": "originaux/wetransfer-1/training grade.mov",
        "log": "originaux/wetransfer-1/training log.mov",
        "decalage": 0,          # mesuré : 0 image sur les plans 1 et 3
        "derniere_image": 296,  # l'image 297 est noire dans les deux versions
        "plans": [[0, 135], [136, 245], [246, 296]],
        # Plan 2 (terrasse) : le LOG a un zoom numérique progressif (x1,000 -> x1,086) absent du GRADED,
        # et son contenu est en avance d'environ 1 image (2 vers la fin). Exclu du comparateur vidéo.
        "plans_exclus": [[136, 245]],
        # Plan 1 (intérieur, caméra fixe) : un seul moment, les autres sont presque identiques (écart <= 5,7/255).
        # Écran partagé (246-296) écarté après test : 2e plan seulement, et son GRADED paraît plus plat que le LOG.
        # Plan 2 (terrasse) écarté : même la meilleure paire (GRADED 137 / LOG 136, même instant)
        # garde un zoom résiduel du LOG de 1 à 2 px aux bords -> pas une correspondance exacte.
        "comparateurs": [
            {"graded": 66},    # 1 : intérieur du fast-food, néons orange
        ],
        "video": [[0, 135], [246, 296]],    # plans 1 et 3 (7,79 s) : seuls plans où LOG et GRADED sont la même image
        # Une image par plan nettement différent : intérieur, terrasse (l'écran partagé est écarté ;
        # deux images de la terrasse seraient presque identiques, caméra fixe).
        "galerie": [30, 228],
    },
}

SRGB_ICC = "/System/Library/ColorSync/Profiles/sRGB Profile.icc"
JPEG_QUALITE = 90
VIDEO_CRF = 24
VIDEO_MAXRATE = "4M"
VIDEO_BUFSIZE = "8M"
BANDE = 16                  # bande noire entre LOG et GRADED (px)
VW, VH = 1280, 720          # taille de chaque moitié du comparateur vidéo
VIGN_W, VIGN_H = 384, 216   # vignettes des comparateurs (depuis le GRADED de chaque paire)

DOSSIER_COMP = "site/media/comparateurs"
DOSSIER_GAL = "site/media/galerie"
DOSSIER_TRAVAIL = "travail/etalonnage"
DOSSIER_PLANCHES = "travail/planches"
FICHIER_ANALYSE = "travail/etalonnage/alignement.json"
FICHIER_VERIF = "travail/etalonnage/verifications.json"
MANIFESTE = "travail/medias-etalonnage.json"

SCALE_RGB = ("scale=in_range=tv:in_color_matrix=bt709:out_range=pc:"
             "flags=lanczos+accurate_rnd+full_chroma_int+full_chroma_inp,format=rgb24")
SCALE_YUV_720 = (f"scale={VW}:{VH}:in_range=tv:out_range=tv:in_color_matrix=bt709:out_color_matrix=bt709:"
                 "flags=lanczos+accurate_rnd+full_chroma_int")
TAGS_COULEUR = ["-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv"]

FORCE = False


# =====================================================================================
# Outils
# =====================================================================================
def chemin(rel):
    return os.path.join(RACINE, rel)


def journal(etape):
    return chemin(f"travail/medias-etalonnage-{etape}.log")


def lancer(cmd, etape, capture=False):
    """Lance une commande ; sortie bavarde dans travail/medias-etalonnage-<etape>.log."""
    with open(journal(etape), "a") as j:
        j.write("\n$ " + " ".join(cmd) + "\n")
        j.flush()
        if capture:
            r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=j)
        else:
            r = subprocess.run(cmd, stdout=j, stderr=j)
    if r.returncode != 0:
        sys.exit(f"Échec ({etape}) : {' '.join(cmd)} — voir {journal(etape)}")
    return r.stdout if capture else None


def dire(msg):
    print(msg, flush=True)


def existe(rel):
    return os.path.exists(chemin(rel)) and os.path.getsize(chemin(rel)) > 0


def ffprobe_json(rel, *args):
    out = subprocess.run(["ffprobe", "-v", "error", "-of", "json", *args, chemin(rel)],
                         stdout=subprocess.PIPE, check=True).stdout
    return json.loads(out)


def selection(nums):
    """Expression select : numéros regroupés en plages contiguës (une expression trop longue fait échouer ffmpeg)."""
    nums = sorted(set(nums))
    plages = []
    for n in nums:
        if plages and n == plages[-1][1] + 1:
            plages[-1][1] = n
        else:
            plages.append([n, n])
    return "+".join(f"eq(n,{a})" if a == b else f"between(n,{a},{b})" for a, b in plages)


def selection_segments(segs, decal=0):
    return "+".join(f"between(n,{a + decal},{b + decal})" for a, b in segs)


def gris(rel, w, h, nums=None, vf_avant=""):
    """Images en niveaux de gris (luma) w x h, toutes ou seulement les numéros donnés -> liste de bytes."""
    vf = ""
    if nums is not None:
        vf += f"select='{selection(nums)}',"
    vf += vf_avant + f"scale={w}:{h}:flags=area,format=gray"
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", chemin(rel), "-map", "0:v:0", "-vf", vf,
                          "-fps_mode", "passthrough", "-f", "rawvideo", "-"],
                         stdout=subprocess.PIPE, check=True).stdout
    n = w * h
    images = [raw[i:i + n] for i in range(0, len(raw), n)]
    if nums is not None:
        if len(images) != len(nums):
            sys.exit(f"Extraction incomplète {rel} : {len(images)} / {len(nums)}")
        return dict(zip(sorted(nums), images))
    return images


def normer(v):
    m = sum(v) / len(v)
    c = [x - m for x in v]
    s = math.sqrt(sum(x * x for x in c)) or 1.0
    return [x / s for x in c]


def contours(f, w, h):
    g = []
    for y in range(h - 1):
        r = y * w
        for x in range(w - 1):
            g.append(abs(f[r + x + 1] - f[r + x]) + abs(f[r + w + x] - f[r + x]))
    return g


def produit(a, b):
    return sum(x * y for x, y in zip(a, b))


# ---- recalage géométrique (zoom + translation) pour vérifier qu'une paire est la même image ----
RW, RH = 240, 135


def _ncc_bloc(a, b, x0, y0, pw, ph, dx, dy):
    sa = sb = sab = saa = sbb = 0.0
    n = 0
    for y in range(y0, y0 + ph):
        ra = y * RW
        rb = (y + dy) * RW + dx
        for x in range(x0, x0 + pw):
            va = a[ra + x]
            vb = b[rb + x]
            sa += va; sb += vb; sab += va * vb; saa += va * va; sbb += vb * vb; n += 1
    d = (saa - sa * sa / n) * (sbb - sb * sb / n)
    return (sab - sa * sb / n) / math.sqrt(d) if d > 0 else 0.0


def recaler(a, b):
    """Estime échelle + translation qui amènent b (LOG) sur a (GRADED), par 15 blocs. -> (s, tx, ty, n_blocs)"""
    R, PW, PH = 10, 36, 26
    pts = []
    for x in (14, 62, 110, 158, 190):
        for y in (12, 54, 96):
            sc, dx, dy = max((_ncc_bloc(a, b, x, y, PW, PH, dx, dy), dx, dy)
                             for dx in range(-R, R + 1) for dy in range(-R, R + 1))
            if sc > 0.6:
                pts.append((x + PW / 2 - RW / 2, y + PH / 2 - RH / 2, dx, dy))
    if len(pts) < 4:
        return 1.0, 0.0, 0.0, len(pts)
    A = [[0.0] * 3 for _ in range(3)]
    B = [0.0] * 3
    for u, v, dx, dy in pts:
        for ligne, val in (((u, 1, 0), dx), ((v, 0, 1), dy)):
            for r in range(3):
                B[r] += ligne[r] * val
                for c in range(3):
                    A[r][c] += ligne[r] * ligne[c]
    M = [A[r] + [B[r]] for r in range(3)]
    for c in range(3):
        p = max(range(c, 3), key=lambda r: abs(M[r][c]))
        M[c], M[p] = M[p], M[c]
        for r in range(3):
            if r != c:
                f = M[r][c] / M[c][c]
                M[r] = [M[r][k] - f * M[c][k] for k in range(4)]
    k, tx, ty = (M[r][3] / M[r][r] for r in range(3))
    return 1 + k, tx, ty, len(pts)


def deformer(b, s, tx, ty):
    out = [None] * (RW * RH)
    for y in range(RH):
        v = y - RH / 2
        for x in range(RW):
            X = s * (x - RW / 2) + RW / 2 + tx
            Y = s * v + RH / 2 + ty
            x0 = int(math.floor(X)); y0 = int(math.floor(Y))
            if 0 <= x0 < RW - 1 and 0 <= y0 < RH - 1:
                fx = X - x0; fy = Y - y0; r = y0 * RW + x0
                out[y * RW + x] = ((b[r] * (1 - fx) + b[r + 1] * fx) * (1 - fy)
                                   + (b[r + RW] * (1 - fx) + b[r + RW + 1] * fx) * fy)
    return out


def ncc_contours(a, bw, marge=12):
    sa = sb = sab = saa = sbb = 0.0
    n = 0
    for y in range(marge, RH - marge - 1):
        r = y * RW
        for x in range(marge, RW - marge - 1):
            if bw[r + x] is None or bw[r + x + 1] is None or bw[r + RW + x] is None:
                continue
            ga = abs(a[r + x + 1] - a[r + x]) + abs(a[r + RW + x] - a[r + x])
            gb = abs(bw[r + x + 1] - bw[r + x]) + abs(bw[r + RW + x] - bw[r + x])
            sa += ga; sb += gb; sab += ga * gb; saa += ga * ga; sbb += gb * gb; n += 1
    return (sab - sa * sb / n) / math.sqrt((saa - sa * sa / n) * (sbb - sb * sb / n))


def test_paire(G, L, kg, kl_centre, rayon, bornes):
    """Recale L[kl_centre] sur G[kg] puis compare G[kg] à L[j] pour j autour : renvoie le détail."""
    s, tx, ty, nb = recaler(G[kg], L[kl_centre])
    scores = {}
    for j in range(kl_centre - rayon, kl_centre + rayon + 1):
        if bornes[0] <= j <= bornes[1] and j in L:
            scores[j] = round(ncc_contours(G[kg], deformer(L[j], s, tx, ty)), 4)
    meilleur = max(scores, key=scores.get)
    return {"graded": kg, "log_teste": kl_centre, "zoom": round(s, 4), "tx_px240": round(tx, 2),
            "ty_px240": round(ty, 2), "blocs": nb, "scores": {str(k): v for k, v in scores.items()},
            "meilleure_log": meilleur, "ecart_mesure": meilleur - kg}


# =====================================================================================
# Étape 1 : analyse de l'alignement LOG / GRADED
# =====================================================================================
def compter(rel):
    d = ffprobe_json(rel, "-select_streams", "v:0", "-count_packets", "-show_entries",
                     "stream=nb_read_packets,duration,width,height,r_frame_rate,pix_fmt,color_range,"
                     "color_space,color_transfer,color_primaries,codec_name,profile")
    return d["streams"][0]


def images_cles(rel):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "frame=pict_type", "-of", "csv=p=0", chemin(rel)],
                         stdout=subprocess.PIPE, check=True).stdout.decode().split()
    return [i for i, t in enumerate(out) if t.strip().startswith("I")]


def luma_moyenne(rel, nums):
    vf = f"select='{selection(nums)}',signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-"
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", chemin(rel), "-map", "0:v:0", "-vf", vf,
                          "-an", "-f", "null", "-"], stdout=subprocess.PIPE, check=True).stdout.decode()
    vals = [float(l.split("=")[1]) for l in out.splitlines() if "YAVG=" in l]
    return dict(zip(nums, vals))


def coupes(images, w, h):
    d = [0.0] + [sum(abs(a - b) for a, b in zip(images[i], images[i - 1])) / (w * h)
                 for i in range(1, len(images))]
    med = sorted(d)[len(d) // 2] or 0.1
    return [i for i, v in enumerate(d) if v > max(10 * med, 20.0)], d


def analyse():
    if existe(FICHIER_ANALYSE) and not FORCE:
        dire(f"analyse : cache {FICHIER_ANALYSE} (relancer avec --force pour refaire)")
        return json.load(open(chemin(FICHIER_ANALYSE)))
    t0 = time.time()
    W, H = 160, 90
    res = {}
    for pid, p in PROJETS.items():
        dire(f"analyse {pid} ...")
        r = {"sources": {"graded": compter(p["graded"]), "log": compter(p["log"])}}
        nG = int(r["sources"]["graded"]["nb_read_packets"])
        nL = int(r["sources"]["log"]["nb_read_packets"])
        r["images_cles"] = {"graded": images_cles(p["graded"]), "log": images_cles(p["log"])}
        fins = list(range(max(0, nG - 3), nG)), list(range(max(0, nL - 3), nL))
        r["luma_dernieres_images"] = {"graded": luma_moyenne(p["graded"], fins[0]),
                                      "log": luma_moyenne(p["log"], fins[1])}
        G = gris(p["graded"], W, H)
        L = gris(p["log"], W, H)
        Gn = [normer(f) for f in G]; Ln = [normer(f) for f in L]
        Ge = [normer(contours(f, W, H)) for f in G]; Le = [normer(contours(f, W, H)) for f in L]
        # 1) décalage global : corrélation moyenne LOG[i+d] / GRADED[i]
        balayage = []
        for d in range(-5, 6):
            idx = [i for i in range(len(G)) if 0 <= i + d < len(L)]
            balayage.append({"d": d,
                             "luma": round(sum(produit(Gn[i], Ln[i + d]) for i in idx) / len(idx), 4),
                             "contours": round(sum(produit(Ge[i], Le[i + d]) for i in idx) / len(idx), 4),
                             "n": len(idx)})
        r["balayage_global"] = balayage
        r["decalage_global"] = max(balayage, key=lambda b: b["contours"])["d"]
        # 2) image par image : meilleure image LOG dans une fenêtre +-3 (contours)
        ecarts = []
        for i in range(len(G)):
            best = max((produit(Ge[i], Le[j]), j - i) for j in range(max(0, i - 3), min(len(L), i + 4)))
            ecarts.append(best[1])
        hist = {}
        for e in ecarts:
            hist[str(e)] = hist.get(str(e), 0) + 1
        r["ecart_image_par_image"] = {"histogramme": hist, "suite": ecarts}
        # 3) changements de plan détectés dans les deux versions
        cG, dG = coupes(G, W, H)
        cL, dL = coupes(L, W, H)
        r["coupes"] = {"graded": cG, "log": cL}
        r["mouvement_graded"] = [round(x, 2) for x in dG]
        # 4) par plan : corrélation des contours à d=0, et recalage zoom/temps sur des images témoins
        Gr = {}; Lr = {}
        plans = []
        temoins = []
        for a, b in p["plans"]:
            exclu = [a, b] in p["plans_exclus"]
            pas = 12 if exclu else max(10, (b - a) // 4)
            t = list(range(a + 2, b - 1, pas))
            temoins += [(a, b, k) for k in t]
            idx = range(a, b + 1)
            plans.append({"plan": [a, b], "exclu": exclu,
                          "contours_d0": round(sum(produit(Ge[i], Le[i]) for i in idx) / len(idx), 4),
                          "luma_d0": round(sum(produit(Gn[i], Ln[i]) for i in idx) / len(idx), 4)})
        nums = sorted({k for _, _, k in temoins})
        numsL = sorted({j for a, b, k in temoins for j in range(k - 3, k + 4) if a <= j <= b})
        Gr = gris(p["graded"], RW, RH, nums)
        Lr = gris(p["log"], RW, RH, numsL)
        details = []
        for a, b, k in temoins:
            details.append(dict(test_paire(Gr, Lr, k, k, 3, (a, b)), plan=[a, b]))
        for pl in plans:
            pl["temoins"] = [d for d in details if d["plan"] == pl["plan"]]
        r["plans"] = plans
        res[pid] = r
    res["duree_analyse_s"] = round(time.time() - t0, 1)
    os.makedirs(chemin(DOSSIER_TRAVAIL), exist_ok=True)
    json.dump(res, open(chemin(FICHIER_ANALYSE), "w"), indent=1)
    dire(f"analyse écrite : {FICHIER_ANALYSE} ({res['duree_analyse_s']} s)")
    return res


# =====================================================================================
# Étape 2 : planches d'images (pour choisir les plans)
# =====================================================================================
def planches():
    os.makedirs(chemin(DOSSIER_PLANCHES), exist_ok=True)
    for pid, p in PROJETS.items():
        for v in ("graded", "log"):
            sortie = f"{DOSSIER_PLANCHES}/etal-{pid}-{v}.jpg"
            if existe(sortie) and not FORCE:
                continue
            nb = 6 if pid == "maroc" else 5
            lignes = 7 if pid == "maroc" else 5
            lancer(["ffmpeg", "-y", "-v", "error", "-i", chemin(p[v]), "-vf",
                    f"select='not(mod(n,12))',scale=320:180,tile={nb}x{lignes}:padding=4:color=white",
                    "-frames:v", "1", chemin(sortie)], "planches")
        # choix retenus : comparateurs (GRADED) puis galerie
        sortie = f"{DOSSIER_PLANCHES}/etal-{pid}-choix.jpg"
        if existe(sortie) and not FORCE:
            continue
        nums = sorted({c["graded"] for c in p["comparateurs"]} | set(p["galerie"]))
        lancer(["ffmpeg", "-y", "-v", "error", "-i", chemin(p["graded"]), "-vf",
                f"select='{selection(nums)}',scale=480:270,tile=3x{math.ceil(len(nums) / 3)}:padding=4:color=white",
                "-fps_mode", "passthrough", "-frames:v", "1", chemin(sortie)], "planches")
    dire("planches : travail/planches/etal-*.jpg")


# =====================================================================================
# Étape 3 : images (comparateurs + galerie) — PNG dans travail/, JPEG sRGB incorporé sans conversion
# =====================================================================================
def png_source(rel_video, n, sortie_png):
    lancer(["ffmpeg", "-y", "-v", "error", "-i", chemin(rel_video), "-map", "0:v:0", "-vf",
            f"select='eq(n,{n})',{SCALE_RGB}", "-fps_mode", "passthrough", "-frames:v", "1",
            "-update", "1", chemin(sortie_png)], "images")


def jpeg_srgb(png, jpg):
    """JPEG qualité ~90 ; profil sRGB INCORPORÉ sans conversion des valeurs (--embedProfile, jamais --matchTo)."""
    lancer(["sips", "-s", "format", "jpeg", "-s", "formatOptions", str(JPEG_QUALITE),
            "--embedProfile", SRGB_ICC, chemin(png), "--out", chemin(jpg)], "images")


def paire(p, c):
    kg = c["graded"]
    kl = c.get("log", kg + p["decalage"])
    return kg, kl


def images():
    os.makedirs(chemin(DOSSIER_COMP), exist_ok=True)
    os.makedirs(chemin(DOSSIER_GAL), exist_ok=True)
    os.makedirs(chemin(f"{DOSSIER_TRAVAIL}/png"), exist_ok=True)
    for pid, p in PROJETS.items():
        for i, c in enumerate(p["comparateurs"], 1):
            kg, kl = paire(p, c)
            for version, k in (("log", kl), ("graded", kg)):
                jpg = f"{DOSSIER_COMP}/{pid}-{i}-{version}.jpg"
                if existe(jpg) and not FORCE:
                    continue
                png = f"{DOSSIER_TRAVAIL}/png/{pid}-{i}-{version}.png"
                png_source(p[version], k, png)
                jpeg_srgb(png, jpg)
                dire(f"  {jpg}  (image {version} n°{k})")
            jpg = f"{DOSSIER_COMP}/{pid}-{i}-vignette.jpg"
            if not existe(jpg) or FORCE:
                png = f"{DOSSIER_TRAVAIL}/png/{pid}-{i}-vignette.png"
                lancer(["ffmpeg", "-y", "-v", "error", "-i", chemin(p["graded"]), "-map", "0:v:0", "-vf",
                        f"select='eq(n,{kg})',{SCALE_RGB.replace('scale=', f'scale={VIGN_W}:{VIGN_H}:', 1)}",
                        "-fps_mode", "passthrough", "-frames:v", "1", "-update", "1", chemin(png)], "images")
                jpeg_srgb(png, jpg)
                dire(f"  {jpg}  (vignette, image graded n°{kg})")
        for i, k in enumerate(p["galerie"], 1):
            jpg = f"{DOSSIER_GAL}/{pid}-{i}.jpg"
            if existe(jpg) and not FORCE:
                continue
            png = f"{DOSSIER_TRAVAIL}/png/galerie-{pid}-{i}.png"
            png_source(p["graded"], k, png)
            jpeg_srgb(png, jpg)
            dire(f"  {jpg}  (image graded n°{k})")
    dire("images : faites")


# =====================================================================================
# Étape 4 : comparateurs vidéo empilés (LOG en haut, bande noire, GRADED en bas) + posters
# =====================================================================================
def videos():
    os.makedirs(chemin(DOSSIER_COMP), exist_ok=True)
    for pid, p in PROJETS.items():
        segs = p["video"]
        d = p["decalage"]
        mp4 = f"{DOSSIER_COMP}/{pid}-video.mp4"
        if not existe(mp4) or FORCE:
            # Même sélection d'images (décalage compensé) sur les deux sources : synchro à l'image par construction.
            fc = (f"[0:v]select='{selection_segments(segs, d)}',setpts=N/{FPS}/TB,{SCALE_YUV_720},"
                  f"pad={VW}:{VH + BANDE}:0:0:color=black[haut];"
                  f"[1:v]select='{selection_segments(segs)}',setpts=N/{FPS}/TB,{SCALE_YUV_720}[bas];"
                  f"[haut][bas]vstack=inputs=2,setsar=1,format=yuv420p,"
                  f"setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv[v]")
            lancer(["ffmpeg", "-y", "-i", chemin(p["log"]), "-i", chemin(p["graded"]),
                    "-filter_complex", fc, "-map", "[v]", "-an",
                    "-c:v", "libx264", "-profile:v", "high", "-level:v", "4.0", "-refs", "4",
                    "-preset", "slow", "-crf", str(VIDEO_CRF),
                    "-maxrate", VIDEO_MAXRATE, "-bufsize", VIDEO_BUFSIZE, "-g", str(FPS),
                    "-pix_fmt", "yuv420p", *TAGS_COULEUR, "-r", str(FPS), "-movflags", "+faststart",
                    chemin(mp4)], "videos")
            dire(f"  {mp4}")
        poster = f"{DOSSIER_COMP}/{pid}-video-poster.jpg"
        if not existe(poster) or FORCE:
            k = segs[0][0]
            png = f"{DOSSIER_TRAVAIL}/png/{pid}-video-poster.png"
            os.makedirs(chemin(f"{DOSSIER_TRAVAIL}/png"), exist_ok=True)
            srgb720 = SCALE_RGB.replace("scale=", f"scale={VW}:{VH}:", 1)
            fc = (f"[0:v]select='eq(n,{k + d})',{srgb720},pad={VW}:{VH + BANDE}:0:0:color=black[haut];"
                  f"[1:v]select='eq(n,{k})',{srgb720}[bas];[haut][bas]vstack=inputs=2[v]")
            lancer(["ffmpeg", "-y", "-v", "error", "-i", chemin(p["log"]), "-i", chemin(p["graded"]),
                    "-filter_complex", fc, "-map", "[v]", "-fps_mode", "passthrough", "-frames:v", "1",
                    "-update", "1", chemin(png)], "videos")
            jpeg_srgb(png, poster)
            dire(f"  {poster}  (image n°{k}, première image de la vidéo)")
    dire("vidéos : faites")


# =====================================================================================
# Étape 5 : vérifications (ffprobe, paires, synchro, couleur)
# =====================================================================================
def rgb(rel, w=None, h=None, vf_extra=""):
    vf = vf_extra + ("," if vf_extra else "") + (f"scale={w}:{h}:flags=area," if w else "") + "format=rgb24"
    return subprocess.run(["ffmpeg", "-v", "error", "-i", chemin(rel), "-vf", vf, "-frames:v", "1",
                           "-f", "rawvideo", "-"], stdout=subprocess.PIPE, check=True).stdout


def ecarts_rgb(a, b, pas=1):
    n = len(a) // 3
    somme = 0
    signe = [0, 0, 0]
    sombre = [0, 0]
    maxi = 0
    cnt = 0
    for i in range(0, n, pas):
        for c in range(3):
            va = a[3 * i + c]; vb = b[3 * i + c]
            e = vb - va
            somme += abs(e); signe[c] += e
            if abs(e) > maxi:
                maxi = abs(e)
            if va < 48:
                sombre[0] += e; sombre[1] += 1
        cnt += 1
    return {"ecart_moyen_abs": round(somme / (3 * cnt), 3),
            "ecart_moyen_signe_RGB": [round(s / cnt, 3) for s in signe],
            "ecart_moyen_signe_ombres": round(sombre[0] / sombre[1], 3) if sombre[1] else None,
            "ecart_max": maxi, "pixels_compares": cnt}


def video_vers_rgb_theorique(rel_video, n, png):
    """Recalcule RGB depuis le YUV brut de la source (BT.709, plage limitée) et compare au PNG."""
    W, H = 1920, 1080
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", chemin(rel_video), "-map", "0:v:0", "-vf",
                          f"select='eq(n,{n})'", "-fps_mode", "passthrough", "-frames:v", "1",
                          "-pix_fmt", "yuv420p", "-f", "rawvideo", "-"], stdout=subprocess.PIPE, check=True).stdout
    Y = raw[:W * H]; U = raw[W * H:W * H + W * H // 4]; V = raw[W * H + W * H // 4:]
    P = rgb(png)
    somme = 0; cnt = 0; signe = 0
    for y in range(1, H - 1, 7):
        for x in range(1, W - 1, 7):
            # chroma : moyenne des 4 échantillons voisins (proche de l'interpolation de swscale)
            cx = x / 2 - 0.25; cy = y / 2 - 0.25
            x0 = int(cx); y0 = int(cy); fx = cx - x0; fy = cy - y0
            x1 = min(x0 + 1, W // 2 - 1); y1 = min(y0 + 1, H // 2 - 1)

            def ch(pl):
                return ((pl[y0 * (W // 2) + x0] * (1 - fx) + pl[y0 * (W // 2) + x1] * fx) * (1 - fy)
                        + (pl[y1 * (W // 2) + x0] * (1 - fx) + pl[y1 * (W // 2) + x1] * fx) * fy)
            yy = (Y[y * W + x] - 16) * 255 / 219
            cb = (ch(U) - 128) * 255 / 224
            cr = (ch(V) - 128) * 255 / 224
            r = yy + 1.5748 * cr
            g = yy - 0.1873 * cb - 0.4681 * cr
            b = yy + 1.8556 * cb
            for c, val in enumerate((r, g, b)):
                v = min(255, max(0, round(val)))
                e = P[3 * (y * W + x) + c] - v
                somme += abs(e); signe += e; cnt += 1
    return {"ecart_moyen_abs": round(somme / cnt, 3), "ecart_moyen_signe": round(signe / cnt, 3),
            "echantillons": cnt}


def mse(a, b):
    return sum((x - y) ** 2 for x, y in zip(a, b)) / len(a)


def geometrie_pleine_def(png_graded, png_log, P=96, R=4):
    """Décalage (px, 1920x1080) de 15 blocs texturés du LOG par rapport au GRADED, puis ajustement
    dx = k*(x-960) + tx, dy = k*(y-540) + ty. Exacte si le déplacement aux bords (k*960) et la translation < 0,5 px."""
    W, H = 1920, 1080

    def lum(p):
        return subprocess.run(["ffmpeg", "-v", "error", "-i", chemin(p), "-vf", "format=gray", "-f", "rawvideo", "-"],
                              stdout=subprocess.PIPE, check=True).stdout
    A = lum(png_graded); B = lum(png_log)

    def grad(f, x0, y0, w, h):
        return [abs(f[y * W + x + 1] - f[y * W + x]) + abs(f[(y + 1) * W + x] - f[y * W + x])
                for y in range(y0, y0 + h) for x in range(x0, x0 + w)]
    blocs = []
    for cx in (160, 560, 960, 1360, 1760):
        for cy in (200, 540, 880):
            x0, y0 = cx - P // 2, cy - P // 2
            fa = grad(A, x0, y0, P, P)
            ma = sum(fa) / len(fa)
            ca = [v - ma for v in fa]
            sa = math.sqrt(sum(v * v for v in ca))
            if sa / math.sqrt(len(fa)) < 2:
                continue   # bloc sans texture (ciel, mur uni)
            gb = grad(B, x0 - R, y0 - R, P + 2 * R, P + 2 * R)
            Q = P + 2 * R
            best = None
            for dy in range(-R, R + 1):
                for dx in range(-R, R + 1):
                    fb = [gb[(y + R + dy) * Q + x + R + dx] for y in range(P) for x in range(P)]
                    mb = sum(fb) / len(fb)
                    sb = math.sqrt(sum((v - mb) ** 2 for v in fb)) or 1
                    c = sum(x * (y - mb) for x, y in zip(ca, fb)) / (sa * sb)
                    if best is None or c > best[0]:
                        best = (c, dx, dy)
            blocs.append({"centre": [cx, cy], "dx": best[1], "dy": best[2], "ncc": round(best[0], 3)})
    # moindres carrés : k (zoom - 1), tx, ty
    A3 = [[0.0] * 3 for _ in range(3)]
    B3 = [0.0] * 3
    for b in blocs:
        u = b["centre"][0] - W / 2; v = b["centre"][1] - H / 2
        for ligne, val in (((u, 1, 0), b["dx"]), ((v, 0, 1), b["dy"])):
            for r in range(3):
                B3[r] += ligne[r] * val
                for c in range(3):
                    A3[r][c] += ligne[r] * ligne[c]
    M = [A3[r] + [B3[r]] for r in range(3)]
    for c in range(3):
        p = max(range(c, 3), key=lambda r: abs(M[r][c]))
        M[c], M[p] = M[p], M[c]
        for r in range(3):
            if r != c:
                f = M[r][c] / M[c][c]
                M[r] = [M[r][k] - f * M[c][k] for k in range(4)]
    k, tx, ty = (M[r][3] / M[r][r] for r in range(3))
    bord = k * W / 2
    return {"blocs": blocs, "blocs_a_zero": sum(1 for b in blocs if b["dx"] == 0 and b["dy"] == 0),
            "zoom_log_sur_graded": round(1 + k, 5), "deplacement_aux_bords_px": round(bord, 2),
            "translation_px": [round(tx, 2), round(ty, 2)],
            "exacte": abs(bord) < 0.5 and abs(tx) < 0.5 and abs(ty) < 0.5}


def verif():
    v = {}
    dire("vérif : ffprobe des médias ...")
    sorties = []
    for pid, p in PROJETS.items():
        for i in range(1, len(p["comparateurs"]) + 1):
            sorties += [f"{DOSSIER_COMP}/{pid}-{i}-log.jpg", f"{DOSSIER_COMP}/{pid}-{i}-graded.jpg",
                        f"{DOSSIER_COMP}/{pid}-{i}-vignette.jpg"]
        sorties += [f"{DOSSIER_COMP}/{pid}-video.mp4", f"{DOSSIER_COMP}/{pid}-video-poster.jpg"]
        sorties += [f"{DOSSIER_GAL}/{pid}-{i}.jpg" for i in range(1, len(p["galerie"]) + 1)]
    probe = {}
    for s in sorties:
        if not existe(s):
            sys.exit(f"Manque : {s}")
        info = ffprobe_json(s, "-show_entries",
                            "stream=codec_name,profile,width,height,pix_fmt,color_range,color_space,color_transfer,"
                            "color_primaries,nb_frames,duration,r_frame_rate,level:format=duration,size,format_name")
        st = info["streams"][0]
        e = {"taille_octets": os.path.getsize(chemin(s)), "largeur": st.get("width"), "hauteur": st.get("height"),
             "codec": st.get("codec_name"), "pix_fmt": st.get("pix_fmt")}
        if s.endswith(".mp4"):
            e.update({"profil": st.get("profile"), "niveau": st.get("level"), "images": int(st.get("nb_frames", 0)),
                      "duree_s": float(info["format"]["duration"]), "ips": st.get("r_frame_rate"),
                      "couleur": [st.get("color_primaries"), st.get("color_transfer"), st.get("color_space"),
                                  st.get("color_range")],
                      "pistes": len(ffprobe_json(s, "-show_entries", "stream=index")["streams"]),
                      "faststart": _faststart(s)})
        else:
            prof = subprocess.run(["sips", "-g", "profile", chemin(s)], stdout=subprocess.PIPE).stdout.decode()
            e["profil_icc"] = prof.strip().splitlines()[-1].split(":", 1)[-1].strip()
        if e["taille_octets"] >= 95 * 1024 * 1024:
            sys.exit(f"Trop gros (>= 95 Mo) : {s}")
        probe[s] = e
    v["ffprobe"] = probe

    # Paires des comparateurs : même image ? (recalage + comparaison aux images voisines)
    dire("vérif : paires LOG/GRADED des comparateurs ...")
    v["paires"] = {}
    for pid, p in PROJETS.items():
        lst = []
        kgs = [paire(p, c)[0] for c in p["comparateurs"]]
        kls = sorted({j for c in p["comparateurs"] for j in range(paire(p, c)[1] - 2, paire(p, c)[1] + 3)
                      if 0 <= j <= p["derniere_image"]})
        G = gris(p["graded"], RW, RH, sorted(set(kgs)))
        L = gris(p["log"], RW, RH, kls)
        for i, c in enumerate(p["comparateurs"], 1):
            kg, kl = paire(p, c)
            plan = next(pl for pl in p["plans"] if pl[0] <= kg <= pl[1])
            t = test_paire(G, L, kg, kl, 2, (plan[0], plan[1]))
            t["n"] = i
            # géométrie en pleine définition (sur les PNG) : décalage de 15 blocs, puis zoom/translation ajustés
            geo = geometrie_pleine_def(f"{DOSSIER_TRAVAIL}/png/{pid}-{i}-graded.png",
                                       f"{DOSSIER_TRAVAIL}/png/{pid}-{i}-log.png")
            t["pleine_def"] = geo
            t["meme_instant"] = t["meilleure_log"] == kl
            t["ok"] = t["meme_instant"] and geo["exacte"]
            lst.append(t)
            if not t["ok"]:
                dire(f"  ATTENTION {pid}-{i} : paire non confirmée {t}")
        v["paires"][pid] = lst

    # Synchro des comparateurs vidéo : à 3 instants, haut = LOG[k], bas = GRADED[k]
    dire("vérif : synchro des comparateurs vidéo ...")
    v["synchro"] = {}
    sw, sh = 640, 360
    for pid, p in PROJETS.items():
        segs = p["video"]; d = p["decalage"]
        carte = [k for a, b in segs for k in range(a, b + 1)]
        mouv = json.load(open(chemin(FICHIER_ANALYSE)))[pid]["mouvement_graded"]
        # instants : l'image la plus mobile de chaque tiers (meilleure discrimination)
        instants = []
        tiers = len(carte) // 3
        for t in range(3):
            plage = range(t * tiers + 2, (t + 1) * tiers - 2)
            m = max(plage, key=lambda m: mouv[carte[m]] if 0 < m < len(carte) - 1 and mouv[carte[m]] < 20 and
                    mouv[carte[m] + 1] < 20 and carte[m - 1] == carte[m] - 1 and carte[m + 1] == carte[m] + 1 else -1)
            instants.append(m)
        mp4 = f"{DOSSIER_COMP}/{pid}-video.mp4"
        haut = gris(mp4, sw, sh, instants, vf_avant=f"crop={VW}:{VH}:0:0,")
        bas = gris(mp4, sw, sh, instants, vf_avant=f"crop={VW}:{VH}:0:{VH + BANDE},")
        ks = sorted({carte[m] + o for m in instants for o in (-1, 0, 1)})
        srcL = gris(p["log"], sw, sh, [k + d for k in ks], vf_avant=SCALE_YUV_720 + ",")
        srcG = gris(p["graded"], sw, sh, ks, vf_avant=SCALE_YUV_720 + ",")
        res = []
        for m in instants:
            k = carte[m]
            eh = {str(k + o): round(mse(haut[m], srcL[k + o + d]), 2) for o in (-1, 0, 1)}
            eb = {str(k + o): round(mse(bas[m], srcG[k + o]), 2) for o in (-1, 0, 1)}
            croise = round(mse(haut[m], srcG[k]), 2)
            res.append({"image_video": m, "temps_s": round(m / FPS, 3), "image_source_attendue": k,
                        "haut_vs_LOG_mse": eh, "bas_vs_GRADED_mse": eb, "haut_vs_GRADED_mse": croise,
                        "ok": min(eh, key=eh.get) == str(k) and min(eb, key=eb.get) == str(k)})
        # bande noire : valeurs Y brutes de la bande (attendu 16 = noir en plage limitée), sans conversion
        brut = subprocess.run(["ffmpeg", "-v", "error", "-i", chemin(mp4), "-vf", f"select='eq(n,{instants[1]})'",
                               "-fps_mode", "passthrough", "-frames:v", "1", "-pix_fmt", "yuv420p",
                               "-f", "rawvideo", "-"], stdout=subprocess.PIPE, check=True).stdout
        raw = brut[VH * VW:(VH + BANDE) * VW]
        # ni image noire : luma moyenne de chaque moitié, image par image (noir = 16)
        lum = {}
        for nom, y0 in (("haut", 0), ("bas", VH + BANDE)):
            out = subprocess.run(["ffmpeg", "-v", "error", "-i", chemin(mp4), "-vf",
                                  f"crop={VW}:{VH}:0:{y0},signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-",
                                  "-an", "-f", "null", "-"], stdout=subprocess.PIPE, check=True).stdout.decode()
            vals = [float(l.split("=")[1]) for l in out.splitlines() if "YAVG=" in l]
            lum[nom] = {"min": round(min(vals), 1), "max": round(max(vals), 1), "images": len(vals)}
        v["synchro"][pid] = {"instants": res, "bande_Y_min_max_moy": [min(raw), max(raw),
                                                                       round(sum(raw) / len(raw), 2)],
                             "luma_moyenne_par_moitie": lum,
                             "sans_noir": all(x["min"] > 30 for x in lum.values())}
        if "carton" in p:
            # carton « The end » : zone du titre (x 890-1029, y 520-559 en 1920x1080) avant / après l'image du carton
            c = p["carton"]
            zone = {}
            for version in ("graded", "log"):
                nums = [c - 2, c - 1, c, c + 1]
                vf = (f"select='{selection(nums)}',crop=140:40:890:520,signalstats,"
                      "metadata=print:key=lavfi.signalstats.YAVG:file=-")
                out = subprocess.run(["ffmpeg", "-v", "error", "-i", chemin(p[version]), "-vf", vf, "-an",
                                      "-f", "null", "-"], stdout=subprocess.PIPE, check=True).stdout.decode()
                vals = [round(float(l.split("=")[1]), 1) for l in out.splitlines() if "YAVG=" in l]
                zone[version] = dict(zip([str(n) for n in nums], vals))
            fin = max(b for _, b in segs)
            v["synchro"][pid]["carton"] = {"image_du_carton": c, "derniere_image_utilisee": fin,
                                           "luma_zone_titre": zone, "sans_carton": fin < c}
        for r in res:
            if not r["ok"]:
                dire(f"  ATTENTION synchro {pid} : {r}")

    # Couleur : source -> PNG (calcul indépendant) et PNG -> JPEG (sips sans conversion)
    dire("vérif : couleur (PNG -> JPEG sur toutes les images, vidéo -> PNG sur une paire) ...")
    v["couleur"] = {"png_vers_jpeg": {}, "video_vers_png": {}}
    for pid, p in PROJETS.items():
        for i in range(1, len(p["comparateurs"]) + 1):
            for version in ("log", "graded", "vignette"):
                png = f"{DOSSIER_TRAVAIL}/png/{pid}-{i}-{version}.png"
                jpg = f"{DOSSIER_COMP}/{pid}-{i}-{version}.jpg"
                if existe(png):
                    v["couleur"]["png_vers_jpeg"][jpg] = ecarts_rgb(rgb(png), rgb(jpg), pas=5)
        for i in range(1, len(p["galerie"]) + 1):
            png = f"{DOSSIER_TRAVAIL}/png/galerie-{pid}-{i}.png"
            jpg = f"{DOSSIER_GAL}/{pid}-{i}.jpg"
            if existe(png):
                v["couleur"]["png_vers_jpeg"][jpg] = ecarts_rgb(rgb(png), rgb(jpg), pas=5)
        png = f"{DOSSIER_TRAVAIL}/png/{pid}-video-poster.png"
        jpg = f"{DOSSIER_COMP}/{pid}-video-poster.jpg"
        if existe(png):
            v["couleur"]["png_vers_jpeg"][jpg] = ecarts_rgb(rgb(png), rgb(jpg), pas=5)
    for pid in PROJETS:
        p = PROJETS[pid]
        kg, kl = paire(p, p["comparateurs"][0])
        for version, k in (("log", kl), ("graded", kg)):
            png = f"{DOSSIER_TRAVAIL}/png/{pid}-1-{version}.png"
            if existe(png):
                v["couleur"]["video_vers_png"][f"{pid}-1-{version}"] = video_vers_rgb_theorique(p[version], k, png)
    json.dump(v, open(chemin(FICHIER_VERIF), "w"), indent=1)
    dire(f"vérif écrite : {FICHIER_VERIF}")
    return v


def _faststart(rel):
    with open(chemin(rel), "rb") as f:
        tete = f.read(1 << 20)
    i_moov = tete.find(b"moov"); i_mdat = tete.find(b"mdat")
    return i_moov != -1 and (i_mdat == -1 or i_moov < i_mdat)


# =====================================================================================
# Étape 6 : manifeste travail/medias-etalonnage.json
# =====================================================================================
def manifeste():
    an = json.load(open(chemin(FICHIER_ANALYSE)))
    ve = json.load(open(chemin(FICHIER_VERIF)))
    pr = ve["ffprobe"]
    m = {"genere_le": time.strftime("%Y-%m-%d %H:%M"), "script": "scripts/medias_etalonnage.py",
         "chemins": "relatifs à site/", "ips": FPS, "projets": {}}
    for pid, p in PROJETS.items():
        a = an[pid]
        e = {
            "sources": {"graded": p["graded"], "log": p["log"],
                        "images_graded": int(a["sources"]["graded"]["nb_read_packets"]),
                        "images_log": int(a["sources"]["log"]["nb_read_packets"])},
            "decalage": {
                "valeur_images": p["decalage"], "convention": "image LOG = image GRADED + décalage",
                "mesure_globale": a["decalage_global"],
                "correlation_contours_par_decalage": {str(b["d"]): b["contours"] for b in a["balayage_global"]},
                "ecart_image_par_image": a["ecart_image_par_image"]["histogramme"],
                "coupes_graded": a["coupes"]["graded"], "coupes_log": a["coupes"]["log"],
                "images_cles_identiques": a["images_cles"]["graded"] == a["images_cles"]["log"],
                "plans": p["plans"], "plans_exclus": p["plans_exclus"],
            },
            "comparateurs_images": [],
            "comparateur_video": None,
            "galerie": [],
        }
        if pid == "maroc":
            e["decalage"]["note"] = ("La 481e image du LOG (n° 480, fin de fichier) est noire (Y=16) ; "
                                     "elle est ignorée. Aucune image de décalage au début. Carton « The end » "
                                     "à partir de l'image 187 (deux versions) : exclu du comparateur vidéo, "
                                     "qui fait donc 7,79 s (tout ce qui précède le carton).")
        if pid == "training":
            e["decalage"]["note"] = ("Plans 1 et 3 : même image (décalage 0). Plan 2 (136-245) : le LOG a un zoom "
                                     "numérique progressif (x1,000 -> x1,086) et une avance de 1 image (2 vers la fin) ; "
                                     "exclu des comparateurs d'images et du comparateur vidéo (la meilleure paire, GRADED 137 / LOG 136, "
                                     "est au même instant mais garde un zoom résiduel de 1 à 2 px aux bords) ; ses images "
                                     "GRADED servent à la galerie. Image 297 noire dans les deux versions. "
                                     "Le LOG du plan 1 porte un texte incrusté « 14:22 » (à gauche) absent du GRADED.")
        for i, c in enumerate(p["comparateurs"], 1):
            kg, kl = paire(p, c)
            ver = next(t for t in ve["paires"][pid] if t["n"] == i)
            e["comparateurs_images"].append({
                "n": i,
                "log": f"media/comparateurs/{pid}-{i}-log.jpg",
                "graded": f"media/comparateurs/{pid}-{i}-graded.jpg",
                "vignette": f"media/comparateurs/{pid}-{i}-vignette.jpg",
                "vignette_taille": [VIGN_W, VIGN_H],
                "vignette_poids_octets": pr[f"{DOSSIER_COMP}/{pid}-{i}-vignette.jpg"]["taille_octets"],
                "image_source_graded": kg, "image_source_log": kl,
                "temps_graded_s": round(kg / FPS, 3), "temps_log_s": round(kl / FPS, 3),
                "largeur": 1920, "hauteur": 1080,
                "poids_octets": [pr[f"{DOSSIER_COMP}/{pid}-{i}-log.jpg"]["taille_octets"],
                                 pr[f"{DOSSIER_COMP}/{pid}-{i}-graded.jpg"]["taille_octets"]],
                "verif_meme_image": {
                    "ok": ver["ok"], "meme_instant": ver["meme_instant"],
                    "scores_log_voisines": ver["scores"],
                    "deplacement_aux_bords_px": ver["pleine_def"]["deplacement_aux_bords_px"],
                    "translation_px": ver["pleine_def"]["translation_px"],
                    "blocs_a_zero": f'{ver["pleine_def"]["blocs_a_zero"]}/{len(ver["pleine_def"]["blocs"])}'},
            })
        mp4 = f"{DOSSIER_COMP}/{pid}-video.mp4"
        poster = f"{DOSSIER_COMP}/{pid}-video-poster.jpg"
        segs = p["video"]
        e["comparateur_video"] = {
            "video": f"media/comparateurs/{pid}-video.mp4",
            "poster": f"media/comparateurs/{pid}-video-poster.jpg",
            "disposition": f"LOG en haut (0-{VH - 1}), bande noire {BANDE} px ({VH}-{VH + BANDE - 1}), "
                           f"GRADED en bas ({VH + BANDE}-{2 * VH + BANDE - 1})",
            "largeur": pr[mp4]["largeur"], "hauteur": pr[mp4]["hauteur"],
            "moitie": {"largeur": VW, "hauteur": VH, "haut_y": 0, "bas_y": VH + BANDE},
            "duree_s": round(pr[mp4]["duree_s"], 3), "images": pr[mp4]["images"],
            "poids_octets": pr[mp4]["taille_octets"], "poster_poids_octets": pr[poster]["taille_octets"],
            "son": False,
            "segments_source_graded": [{"images": [a_, b_], "temps_s": [round(a_ / FPS, 3), round((b_ + 1) / FPS, 3)]}
                                       for a_, b_ in segs],
            "segments_source_log": [[a_ + p["decalage"], b_ + p["decalage"]] for a_, b_ in segs],
            "encodage": {"codec": pr[mp4]["codec"], "profil": pr[mp4]["profil"], "niveau": pr[mp4]["niveau"],
                         "pix_fmt": pr[mp4]["pix_fmt"], "couleur": pr[mp4]["couleur"], "crf": VIDEO_CRF,
                         "faststart": pr[mp4]["faststart"]},
            "verif_synchro": ve["synchro"][pid],
        }
        for i, k in enumerate(p["galerie"], 1):
            g = f"{DOSSIER_GAL}/{pid}-{i}.jpg"
            e["galerie"].append({"chemin": f"media/galerie/{pid}-{i}.jpg", "projet": pid, "image_source_graded": k,
                                 "temps_s": round(k / FPS, 3), "largeur": pr[g]["largeur"],
                                 "hauteur": pr[g]["hauteur"], "poids_octets": pr[g]["taille_octets"]})
        m["projets"][pid] = e
    m["couleur"] = {"regle": "aucun LUT, aucun filtre, aucune correction ; JPEG avec profil sRGB incorporé sans "
                             "conversion (sips --embedProfile) ; vidéos H.264 High yuv420p BT.709 plage limitée",
                    "video_vers_png": ve["couleur"]["video_vers_png"],
                    "png_vers_jpeg_ecart_moyen_max": max(x["ecart_moyen_abs"] for x in
                                                         ve["couleur"]["png_vers_jpeg"].values())}
    json.dump(m, open(chemin(MANIFESTE), "w"), indent=1, ensure_ascii=False)
    dire(f"manifeste écrit : {MANIFESTE}")


# =====================================================================================
ETAPES = {"analyse": analyse, "planches": planches, "images": images, "videos": videos,
          "verif": verif, "manifeste": manifeste}

if __name__ == "__main__":
    args = sys.argv[1:]
    if "--force" in args:
        FORCE = True
        args.remove("--force")
    inconnues = [a for a in args if a not in ETAPES]
    if inconnues:
        sys.exit(f"Étape inconnue : {inconnues}. Étapes : {' '.join(ETAPES)}")
    os.chdir(RACINE)
    for nom in (args or list(ETAPES)):
        ETAPES[nom]()
