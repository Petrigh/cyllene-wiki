#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera assets/img/map-height.png a partir de tools/map-tiers.png.

Herramienta de autor. No es parte del sitio (_config.yml excluye tools/), pero
su SALIDA si se publica: el heightmap que levanta la malla 3D de la home.

----------------------------------------------------------------------------
POR QUE EXISTE ESTO
----------------------------------------------------------------------------

El heightmap NO se pinta a mano. Se pinto a mano una vez y se vio por que no
hay que hacerlo: el gris es la variable equivocada. El gris fija la ALTURA, y
lo que hace que un terreno se lea no es la altura sino la PENDIENTE --altura
sobre distancia-- que ningun pincel controla. De ahi salian las cuatro cosas
que se veian mal:

  - Las montanas eran manchas casi blancas (gris 245) apoyadas sobre tierra
    gris 41: un salto de 200 niveles en un pixel. A la resolucion de la malla
    eso es una pared vertical, y computeVertexNormals la sombrea como tal
    porque LO ES.
  - La costa era un escalon 0 -> 41, igual de vertical.
  - El degrade del noreste no seguia el dibujo. No podia: la herramienta de
    degrade interpola en el espacio de la PANTALLA, en linea recta, y una
    costa es una forma cualquiera. Lo que hace falta es un degrade en el
    espacio de la DISTANCIA A LA COSTA, que ningun pincel da.
  - Ese degrade bajaba hasta negro y cruzaba el nivel del agua: 569 pixeles de
    tierra pintada quedaron abajo del mar.

Asi que aca se pinta OTRA cosa: tools/map-tiers.png, con relleno plano, un
color por escalon de terreno. El balde dibuja eso con precision y se corrige
en dos clicks. Las pendientes las fabrica este script con una transformada de
distancia, y salen continuas y acotadas por construccion.

LA IDEA QUE HAY QUE INTERNALIZAR:

    La pendiente la da el ANCHO de la banda que pintas, no su color.

Para que las montanas se fundan con la llanura no se baja el gris: se pinta
una banda de colinas MAS ANCHA alrededor. El script reparte la subida a lo
largo del ancho que le des.

----------------------------------------------------------------------------
COMO FUNCIONA
----------------------------------------------------------------------------

Para cada pixel del escalon t:

    d_lo = distancia al pixel mas cercano de un escalon MENOR
    d_hi = distancia al pixel mas cercano de un escalon MAYOR
    t_hi = el escalon de ESE pixel mas cercano
    w    = d_lo / (d_lo + d_hi)
    h    = lerp(H[t], H[t_hi], smoothstep(w))

Tres detalles cargan todo el peso. No son adorno, se midieron:

 1. smoothstep, NO un lerp lineal. Los centros de pixel estan a 1 de
    distancia, asi que el ultimo pixel del escalon t-1 no cae en w = 1 exacto
    sino en w = D/(D+1). Con lerp lineal el residuo es 1/D --12% de un escalon
    con D=8, o sea una repisa de un pixel en CADA borde--. Con smoothstep,
    smoothstep(1-e) = 1 - 3e^2 + 2e^3, el residuo pasa a 3/D^2: 4.7%, y cae al
    cuadrado. Si alguien "simplifica" esto a un lerp vuelven las repisas.

 2. El pin de arriba es H[t_hi], NO H[t+1]. Si se pinta una mancha de montana
    directo sobre la tierra baja sin el anillo de colinas --el error natural
    con el balde-- clavar H[t+1] produce un acantilado de 0.393 del rango
    completo en un pixel: exactamente la patologia que esto viene a arreglar,
    reproducida por su reemplazo. Apuntando al escalon que REALMENTE toca, los
    dos lados coinciden y el salto se vuelve una rampa larga y continua. Para
    escalones consecutivos esto es identico a H[t+1], asi que en el caso normal
    no cambia nada.

 3. La normalizacion es POR COMPONENTE CONEXA, no global. Con el campo global,
    el d_hi de una isla es la distancia cruzando el oceano hasta las colinas
    del continente: medido, una isla queda de 0.0006 de alto donde el
    continente con los mismos escalones sube 0.08. Un panqueque. Por eso cada
    componente se clasifica mirando SU borde:

        tiene menor y mayor -> pendiente normal
        solo menor          -> DOMO  (las cumbres, y toda isla, y toda meseta
                                      que sea el punto mas alto de su zona)
        solo mayor          -> CUENCA (el mar, y cualquier hoya cerrada)
        ninguno             -> plano, y se avisa

    Un mecanismo, tres problemas. Y la cuenca aplicada al mar es regalo: el
    fondo deja de ser una chapa plana en 0 y pasa a ser una plataforma que se
    hunde al alejarse de la costa.

El nivel del mar es ESTRUCTURAL, no un recorte: SEA_LEVEL == H[1], el piso del
primer escalon de tierra. La tierra queda >= SEA_LEVEL por construccion, asi
que el bug de la tierra hundida no es algo que haya que vigilar: es
irrepresentable. El assert que hay mas abajo esta para cazar errores de este
script, no del dibujo.

Dos cosas que ESE assert no puede ver, y que son las dos formas en que el mapa
siguio apareciendo hundido:

  - Que la mascara diga "mar" donde el dibujo dice tierra. Para el script esos
    pixeles no son tierra, asi que el invariante se cumple y el mapa igual sale
    inundado. Es lo que hace el umbral de --trace: ver TRACE_SEA_CUT, que ahora
    reporta cuanto descarta.
  - Que el sitio lea este heightmap con OTRO nivel del mar. El gris vive en el
    PNG, pero la altura del plano de agua sale de map_3d_sea en _config.yml. Lo
    verifica check_config(), y --write-config lo corrige.

----------------------------------------------------------------------------
USO
----------------------------------------------------------------------------

    pip install -r tools/requirements.txt

    python tools/make_heightmap.py --trace     # borrador desde lo que ya hay
    python tools/make_heightmap.py --check     # valida mascara y nivel del mar
    python tools/make_heightmap.py             # genera el heightmap
    python tools/make_heightmap.py --report    # genera + diagnostico + debug
    python tools/make_heightmap.py --write-config   # corrige map_3d_sea

Ver tools/README.md para como se pinta la mascara.
"""

import argparse
import hashlib
import os
import re
import sys

import numpy as np
from PIL import Image, PngImagePlugin
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

TIERS_PNG  = os.path.join(HERE, 'map-tiers.png')
DRAFT_PNG  = os.path.join(HERE, 'map-tiers-draft.png')
WATERCOLOR = os.path.join(ROOT, 'assets', 'img', 'map.jpg')
HEIGHT_PNG = os.path.join(ROOT, 'assets', 'img', 'map-height.png')
CONFIG_YML = os.path.join(ROOT, '_config.yml')

# ---------------------------------------------------------------------------
# La paleta y la tabla de alturas. Esto es DATO DE ARTE: es lo que se toca
# cuando el relieve no se ve bien, y es casi lo unico que hay que tocar.
# ---------------------------------------------------------------------------

# Colores lo mas separados posible entre si, a proposito: la mascara se snapea
# al color de paleta mas cercano en RGB, y dos verdes parecidos se
# intercambiarian solo con que el balde deje un borde suavizado.
PALETTE = [
    (0x00, 0x00, 0x00),   # 0 abismo / mar
    (0x00, 0x00, 0xFF),   # 1 plataforma / playa
    (0x00, 0xFF, 0x00),   # 2 tierra baja
    (0xFF, 0xFF, 0x00),   # 3 llanura
    (0xFF, 0x80, 0x00),   # 4 colinas
    (0xFF, 0x00, 0x00),   # 5 montanas
    (0xFF, 0xFF, 0xFF),   # 6 cumbres
]

NAMES = ['abismo/mar', 'plataforma', 'tierra baja', 'llanura',
         'colinas', 'montanas', 'cumbres']

# H son alturas de BORDE, con len(PALETTE)+1 entradas: el escalon t ocupa la
# banda [H[t], H[t+1]]. Asi el escalon de arriba tiene pin superior y
# desaparece la pregunta de "a que apunta la cumbre". Es la clave del esquema.
#
# El espaciado es a proposito NO uniforme --apretado cerca del mar, ancho en la
# montana--. Escalones equiespaciados mas el smoothstep, que tiene pendiente
# cero en cada contorno, se leen como una torta de casamiento.
H = [
    0.00,   # piso del mar
    0.25,   # <-- NIVEL DEL MAR. piso de la plataforma, techo del mar
    0.29,   # +0.04  playa: casi plana, para que la costa se tienda
    0.35,   # +0.06
    0.44,   # +0.09
    0.56,   # +0.12
    0.70,   # +0.14
    0.82,   # +0.12  techo de las cumbres
]
# Los pasos crecen hacia arriba (0.04, 0.06, 0.09, 0.12, 0.14, 0.12): la costa
# sale tendida y la ladera se va parando, que es como se lee un continente.
# Con TRACE_BAND_PX = 14 ninguna banda pasa de ~47 grados.
#
# El techo es 0.82 y no 1.00 a proposito: la queja era que las montanas eran
# demasiado altas. Contra la base de tierra en 0.29 esto da una relacion
# llanura-a-cumbre de 1:2.8, donde el heightmap pintado a mano daba 1:6 (41 vs
# 245). El 18% de rango que sobra no se usa: mas vale tener el nivel del mar en
# un 0.25 exacto que exprimir el ultimo bit.

SEA_LEVEL = H[1]

# Ancho, en pixeles de la mascara, en el que la cuenca del mar baja de la costa
# al fondo. Con la normalizacion por componente el oceano entero seria un plato
# larguisimo y la costa quedaria casi al ras del agua por cientos de pixeles:
# un barrial. Con esto hay plataforma continental y despues llanura abisal.
BOWL_SPAN_PX = 45

# Lo mismo para el domo, pero gobierna la ALTURA que alcanza la cumbre: un
# componente que mide menos de esto de radio no llega al techo de su escalon.
# Sin este tope un pico angosto sube todo el escalon en los pocos pixeles que
# tiene de radio --medido: 66.5 grados en la cumbre, una pared-- y la
# correccion fisicamente correcta no es tenderlo sino que sea MAS BAJO, que es
# lo que pasa con un pico angosto de verdad.
DOME_SPAN_PX = 16

# Radio del desenfoque final, en pixeles de la mascara. NO es decorativo: el
# campo es C1 cruzando los bordes --el smoothstep anula la derivada ahi-- pero
# tiene un pliegue en el EJE MEDIO de cada region, donde los campos d_lo y d_hi
# se doblan. Sin esto, computeVertexNormals dibuja una arista de luz por el
# lomo de cada llanura.
BLUR_PX = 4.0
# 4.0 medido contra la mascara real: la pendiente maxima baja de 55.6 a 52.5
# grados y la reparacion de orilla sigue en 0.09%. Mas arriba (5.5, 7) la
# pendiente casi no mejora y el desenfoque empieza a comerse la costa en serio
# (0.20%, 0.36%). A 1252 de ancho, 4 px son ~1.2 px de la malla: no se pierde
# nada que la malla pueda ver.

# Salida. La malla tiene 384 segmentos de ancho, asi que 640 ya sobra; ademas
# bajar de 1252 promediando suaviza la costa de arriba.
OUT_W, OUT_H = 640, 460

# Distancia RGB maxima tolerada al snapear a la paleta. Mas que esto no es
# "el balde quedo un poco corrido", es un color que no esta en la paleta.
SNAP_TOLERANCE = 60

# Componentes de menos de esto se consideran suciedad y se reasignan. Para una
# transformada de distancia un pixel suelto es catastrofico: un pixel de
# montana en el oceano no solo hace un pincho, deforma el campo d_hi de toda la
# region alrededor.
MIN_COMPONENT_PX = 8

# Ancho minimo, en pixeles, de cada banda que fabrica --trace. Es la perilla de
# "cuanto se funden las cosas": mas ancho, laderas mas tendidas.
TRACE_BAND_PX = 14

# Gris por debajo del cual --trace considera que el heightmap de origen dice
# "mar". No es cero porque el heightmap pintado a mano tiene ruido de
# compresion y bordes de pincel en los grises muy bajos.
#
# Pero ojo con lo que este numero hace: todo lo que el dibujo pinto ENTRE 1 y
# esto se convierte en oceano. En el heightmap pintado a mano eso son
# exactamente 569 px --los mismos 569 que el encabezado nombra como el bug
# original, "tierra pintada abajo del agua"--, o sea que el borrador no arregla
# ese bug, lo cambia de forma: lo que era tierra hundida pasa a ser mar. Se ve
# igual en la malla, y ni el assert ni el reporte lo ven, porque para ellos
# esos pixeles ya no son tierra. Por eso trace() los lista uno por uno: es la
# unica parte del camino donde esa informacion todavia existe.
TRACE_SEA_CUT = 8.0

EIGHT = np.ones((3, 3), bool)


def smoothstep(w):
    """3w^2 - 2w^3. Ver el punto 1 del encabezado: esto es lo que hace que los
    bordes cierren. No cambiar por un lerp."""
    w = np.clip(w, 0.0, 1.0)
    return w * w * (3.0 - 2.0 * w)


# ---------------------------------------------------------------------------
# Entrada / salida
# ---------------------------------------------------------------------------

def read_tiers(path):
    """Lee la mascara y devuelve un array de escalones (int8).

    Acepta cualquier modo de color: todo se pasa a RGB y se snapea al color de
    paleta mas cercano. Una mascara indexada que el editor reordeno, un borde
    suavizado o un balde un poco corrido se resuelven solos; un color que no
    esta en la paleta es un ERROR, no un snapeo silencioso.
    """
    im = Image.open(path)
    if im.mode == 'P':
        im = im.convert('RGBA')
    rgb = np.asarray(im.convert('RGB')).astype(np.int32)

    pal = np.asarray(PALETTE, np.int32)                      # (P, 3)
    d2 = ((rgb[:, :, None, :] - pal[None, None, :, :]) ** 2).sum(-1)
    tier = d2.argmin(-1).astype(np.int8)
    worst = np.sqrt(d2.min(-1))

    bad = worst > SNAP_TOLERANCE
    if bad.any():
        ys, xs = np.nonzero(bad)
        sample = ', '.join(
            '(%d,%d)=#%02X%02X%02X' % (int(xs[i]), int(ys[i]), *rgb[ys[i], xs[i]])
            for i in range(min(5, len(xs))))
        die('%d pixeles con un color que no esta en la paleta (distancia > %d).\n'
            '  Ejemplos: %s\n'
            '  Suele ser antialiasing o un JPEG. La mascara se guarda como PNG,\n'
            '  con el balde y el lapiz, y con el suavizado APAGADO.'
            % (bad.sum(), SNAP_TOLERANCE, sample))
    return tier


def write_gray_png(path, field01, meta):
    """Escribe el campo 0..1 como PNG gris de 8 bits SIN alfa (color type 0).

    El archivo viejo era tipo 4 (gris+alfa) y gastaba ~8 KB en un canal alfa
    constante. Ademas el sampler del navegador lee el canal rojo de un canvas
    (campaign_map_3d.html, 'f[i] = d[i * 4] / 255') y getImageData puede
    poner en cero los canales de color donde el alfa es cero: sin alfa, esa
    clase de bug no se puede ni escribir.
    """
    arr = np.clip(np.rint(field01 * 255.0), 0, 255).astype(np.uint8)
    info = PngImagePlugin.PngInfo()
    for k, v in meta.items():
        info.add_text(str(k), str(v))
    Image.fromarray(arr, mode='L').save(path, 'PNG', optimize=True, pnginfo=info)
    return arr


def short(path):
    """Ruta relativa a la raiz del repo, salvo que caiga afuera --un
    --trace-src en /tmp-- donde una relativa seria una escalera de '..'."""
    rel = os.path.relpath(path, ROOT)
    return path if rel.startswith('..') else rel


def die(msg):
    sys.stderr.write('\nmake_heightmap: ' + msg + '\n\n')
    sys.exit(1)


# ---------------------------------------------------------------------------
# Limpieza y validacion de la mascara
# ---------------------------------------------------------------------------

def despeckle(tier, min_px=MIN_COMPONENT_PX):
    """Reasigna los componentes mas chicos que min_px al escalon del vecino
    conservado mas cercano. Devuelve (tier, informe) y NO lo hace en silencio:
    un pixel suelto que aparece solo es una mancha del pincel, pero cientos
    son sintoma de que la mascara se guardo como JPEG."""
    keep = np.zeros(tier.shape, bool)
    report = []
    for t in range(len(PALETTE)):
        region = tier == t
        if not region.any():
            continue
        lab, n = ndi.label(region, structure=EIGHT)
        sizes = np.bincount(lab.ravel(), minlength=n + 1)
        big = np.zeros(n + 1, bool)
        big[1:] = sizes[1:] >= min_px
        keep |= big[lab]
        n_small = int((~big[1:]).sum())
        if n_small:
            report.append((t, n_small, int(sizes[1:][~big[1:]].sum())))

    if keep.all() or not keep.any():
        return tier, report
    idx = ndi.distance_transform_edt(~keep, return_indices=True)[1]
    out = tier.copy()
    nearest = tier[idx[0], idx[1]]
    out[~keep] = nearest[~keep]
    return out, report


def validate(tier, debug_path=None):
    """Devuelve la lista de problemas. Vacia = la mascara sirve."""
    problems = []

    # 1. El anillo exterior tiene que ser mar. El plano de agua mide
    #    MAP_W * 1.6 (campaign_map_3d.html) y con un nivel del mar de verdad
    #    corta el borde del mapa: si ahi hay tierra se ve el canto de la malla,
    #    que no tiene faldon.
    border = np.concatenate([tier[0, :], tier[-1, :], tier[:, 0], tier[:, -1]])
    if (border != 0).any():
        problems.append('el anillo exterior no es todo mar: %d pixeles del borde '
                        'tienen escalon > 0' % int((border != 0).sum()))

    # 2. Escalones usados. Un escalon interior sin pintar deja vacio uno de los
    #    dos conjuntos de semillas y el cociente se vuelve NaN.
    used = sorted(set(np.unique(tier).tolist()))
    for t in range(min(used), max(used) + 1):
        if t not in used:
            problems.append('el escalon %d (%s) no se uso, pero si se usaron el '
                            '%d y el %d: queda un hueco en la numeracion'
                            % (t, NAMES[t], min(used), max(used)))

    # 3. Saltos de nivel. Es LA regla: si dos escalones que se tocan difieren en
    #    mas de uno, falta pintar la banda del medio, y ahi es donde salen los
    #    acantilados que todo esto viene a eliminar.
    t32 = tier.astype(np.int16)
    jump = np.zeros(tier.shape, bool)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            sh = np.roll(np.roll(t32, dy, 0), dx, 1)
            if dy:
                (sh[0, :] if dy > 0 else sh[-1, :]).fill(0)
            if dx:
                (sh[:, 0] if dx > 0 else sh[:, -1]).fill(0)
            jump |= np.abs(sh - t32) > 1
    if jump.any():
        ys, xs = np.nonzero(jump)
        sample = ', '.join('(%d,%d)' % (int(xs[i]), int(ys[i]))
                           for i in range(min(6, len(xs))))
        problems.append(
            '%d pixeles donde dos escalones que se tocan saltan mas de un nivel.\n'
            '    Ejemplos: %s\n'
            '    Falta pintar la banda intermedia. Es exactamente el error que\n'
            '    produce los acantilados: pintar la montana directo sobre la\n'
            '    llanura sin el anillo de colinas.' % (int(jump.sum()), sample))
        if debug_path:
            vis = np.asarray(tier_to_rgb(tier))
            vis = vis.copy()
            vis[ndi.binary_dilation(jump, np.ones((5, 5), bool))] = (255, 0, 255)
            Image.fromarray(vis).save(debug_path)
            problems.append('se marcaron en magenta en %s'
                            % os.path.relpath(debug_path, ROOT))
    return problems


def tier_to_rgb(tier):
    pal = np.asarray(PALETTE, np.uint8)
    return pal[np.clip(tier, 0, len(PALETTE) - 1)]


# ---------------------------------------------------------------------------
# El generador
# ---------------------------------------------------------------------------

def build_height(tier, verbose=False):
    """Mascara de escalones -> campo de alturas 0..1. Ver el encabezado."""
    h = np.zeros(tier.shape, np.float64)
    Harr = np.asarray(H, np.float64)
    kinds = {}

    for t in range(len(PALETTE)):
        region = tier == t
        if not region.any():
            continue

        lower = tier < t
        higher = tier > t

        # distance_transform_edt mide hasta el CERO mas cercano, de ahi el ~.
        # return_indices da las coordenadas de ese cero, o sea el escalon que
        # realmente toca: es el t_hi del punto 2 del encabezado.
        if lower.any():
            d_lo = ndi.distance_transform_edt(~lower)
        else:
            d_lo = np.zeros(tier.shape)
        if higher.any():
            d_hi, idx = ndi.distance_transform_edt(~higher, return_indices=True)
            top_hi = Harr[tier[idx[0], idx[1]]]
        else:
            d_hi = np.zeros(tier.shape)
            top_hi = np.full(tier.shape, H[t + 1])

        lab, n = ndi.label(region, structure=EIGHT)
        index = np.arange(1, n + 1)
        near_lo = ndi.binary_dilation(lower, EIGHT) if lower.any() else np.zeros(tier.shape, bool)
        near_hi = ndi.binary_dilation(higher, EIGHT) if higher.any() else np.zeros(tier.shape, bool)

        def per_comp(arr):
            return np.atleast_1d(np.asarray(ndi.maximum(arr, lab, index), np.float64))

        has_lo = per_comp(near_lo.astype(np.uint8)) > 0.5
        has_hi = per_comp(near_hi.astype(np.uint8)) > 0.5
        mx_lo = per_comp(d_lo)
        mx_hi = per_comp(d_hi)

        li = lab[region] - 1
        dlo = d_lo[region]
        dhi = d_hi[region]
        thi = top_hi[region]
        hl, hh = has_lo[li], has_hi[li]

        base = H[t]
        w = np.zeros(li.shape, np.float64)
        top = np.full(li.shape, H[t + 1], np.float64)

        normal = hl & hh
        dome = hl & ~hh
        bowl = ~hl & hh
        flat = ~hl & ~hh

        s = np.maximum(dlo + dhi, 1e-12)
        w[normal] = dlo[normal] / s[normal]
        top[normal] = thi[normal]

        # Domo: sube del borde del COMPONENTE a su eje medio. El maximo se toma
        # sobre el componente, nunca global: con un maximo global el macizo mas
        # grande del mapa fija la escala y todo pico chico vuelve a ser un
        # panqueque.
        radius = mx_lo[li][dome]
        w[dome] = np.clip(dlo[dome] / np.maximum(radius, 1e-12), 0, 1)
        top[dome] = base + (H[t + 1] - base) * np.clip(radius / DOME_SPAN_PX, 0, 1)

        # Cuenca: baja del borde hacia adentro. El tope del tramo es
        # BOWL_SPAN_PX, asi el mar tiene plataforma y despues fondo.
        span = np.minimum(np.maximum(mx_hi[li][bowl], 1e-12), float(BOWL_SPAN_PX))
        w[bowl] = 1.0 - np.clip(dhi[bowl] / span, 0, 1)
        top[bowl] = thi[bowl]

        w[flat] = 0.0

        h[region] = base + (top - base) * smoothstep(w)

        kinds[t] = (n, int(normal.sum()), int(dome.sum()),
                    int(bowl.sum()), int(flat.sum()))
        if verbose:
            print('  escalon %d %-12s %5d componentes  normal/domo/cuenca/plano '
                  '= %d/%d/%d/%d'
                  % (t, NAMES[t], n, normal.sum(), dome.sum(), bowl.sum(), flat.sum()))
        if flat.any():
            print('  aviso: %d pixeles del escalon %d (%s) no tocan ningun otro '
                  'escalon; quedan planos.' % (int(flat.sum()), t, NAMES[t]))

    # El nivel del mar es estructural: esto caza errores de ESTE script, no del
    # dibujo. Si salta, el bug esta aca arriba, no en la mascara.
    land = tier >= 1
    if land.any():
        lo = float(h[land].min())
        assert lo >= SEA_LEVEL - 1e-9, (
            'bug del generador: hay tierra en %.6f, debajo del nivel del mar %.3f'
            % (lo, SEA_LEVEL))
    return h, kinds


def finish(h, tier, blur_px=BLUR_PX, out_size=(OUT_W, OUT_H)):
    """Desenfoque, reparacion de la orilla y bajada de resolucion."""
    blurred = ndi.gaussian_filter(h, blur_px) if blur_px > 0 else h

    # El desenfoque es lineal y cruza la orilla, donde el mar cae rapido: tira
    # para abajo una tira finita de playa. La garantia estructural ya hizo su
    # trabajo antes del blur; esto es una reparacion de uno o dos pixeles al
    # borde del agua, y se INFORMA, para que si alguna vez deja de ser
    # marginal se vea en el reporte en vez de quedar tapado.
    land = tier >= 1
    sunk = land & (blurred < SEA_LEVEL)
    repaired = int(sunk.sum())
    blurred = np.where(sunk, SEA_LEVEL, blurred)

    small = np.asarray(
        Image.fromarray(blurred.astype(np.float32), mode='F')
             .resize(out_size, Image.Resampling.BOX),
        np.float64)

    # Bajar de resolucion promedia: un pixel de la costa mezcla tierra y mar y
    # cae abajo del nivel del mar aunque a resolucion plena estuviera arriba.
    # Son pixeles que son mitad agua, asi que dejarlos AL ras del agua es lo
    # correcto; lo que no se puede es que el mapa publicado viole el invariante.
    small_land = np.asarray(
        Image.fromarray((tier >= 1).astype(np.uint8) * 255)
             .resize(out_size, Image.Resampling.NEAREST), np.uint8) > 127
    sunk2 = small_land & (small < SEA_LEVEL)
    repaired += int(sunk2.sum())
    small = np.where(sunk2, SEA_LEVEL, small)
    return np.clip(small, 0.0, 1.0), repaired


# ---------------------------------------------------------------------------
# Diagnostico
# ---------------------------------------------------------------------------

def report(field, tier_small, relief=0.12, seg_x=384):
    arr = np.rint(field * 255).astype(np.int32)
    print('\n--- reporte -------------------------------------------------------')
    print('  salida            %d x %d, gris %d..%d'
          % (field.shape[1], field.shape[0], arr.min(), arr.max()))

    step = max(int(np.abs(np.diff(arr, axis=1)).max()),
               int(np.abs(np.diff(arr, axis=0)).max()))
    print('  salto maximo entre pixeles vecinos   %d niveles  (antes: 164)' % step)

    # Pendiente a la resolucion a la que la malla realmente la ve. MAP_D = 2 y
    # RELIEF = relief * MAP_D, y el ancho de celda sale de los segmentos.
    hgt, wid = field.shape
    map_d, map_w = 2.0, 2.0 * wid / hgt
    seg_z = int(round(seg_x * map_d / map_w))
    mesh = np.asarray(
        Image.fromarray(field.astype(np.float32), mode='F')
             .resize((seg_x + 1, seg_z + 1), Image.Resampling.BOX), np.float64)
    dx = map_w / seg_x
    dz = map_d / seg_z
    dy = relief * map_d
    gx = np.abs(np.diff(mesh, axis=1)) * dy / dx
    gz = np.abs(np.diff(mesh, axis=0)) * dy / dz
    slope = np.degrees(np.arctan(max(gx.max(), gz.max())))
    p999 = np.degrees(np.arctan(np.percentile(np.concatenate(
        [gx.ravel(), gz.ravel()]), 99.9)))
    print('  pendiente maxima en la malla         %.1f grados  (p99.9: %.1f)'
          % (slope, p999))
    if slope > 55:
        print('    ^ arriba de ~55 el ojo lee "pared" en vez de "monte".')
        print('      Ensanchar la banda que este parada, no bajar su color.')

    land = tier_small >= 1
    below = int((land & (arr < round(SEA_LEVEL * 255))).sum())
    print('  nivel del mar                        %.3f  (gris %d)'
          % (SEA_LEVEL, round(SEA_LEVEL * 255)))
    print('  pixeles de tierra bajo el agua       %d   <-- tiene que ser 0  '
          '(antes: 569)' % below)
    print('-------------------------------------------------------------------\n')
    return below


def debug_composite(tier, path):
    """Los bordes de los escalones sobre la acuarela despintada. Un corrimiento
    de 10 px entre la costa dibujada y el borde del escalon 0 es invisible una
    vez generado el heightmap, pero deja la linea de agua en el lugar
    equivocado."""
    if not os.path.exists(WATERCOLOR):
        return None
    wc = Image.open(WATERCOLOR).convert('L').resize(
        (tier.shape[1], tier.shape[0]), Image.Resampling.BILINEAR)
    base = np.asarray(wc, np.float64)[:, :, None] * np.ones(3)
    base = (base * 0.45 + 140).clip(0, 255)

    edges = np.zeros(tier.shape, bool)
    for dy, dx in ((0, 1), (1, 0)):
        sh = np.roll(np.roll(tier, dy, 0), dx, 1)
        edges |= sh != tier
    coast = edges & ndi.binary_dilation(tier == 0, EIGHT) & (tier >= 1)

    out = base.copy()
    out[edges] = (40, 40, 40)
    out[ndi.binary_dilation(coast, EIGHT)] = (255, 0, 0)
    Image.fromarray(out.astype(np.uint8)).save(path)
    return path


# ---------------------------------------------------------------------------
# --trace: el borrador
# ---------------------------------------------------------------------------

def grow_apron(target, land, band_px):
    """Le pone a cada cosa alta el faldon que necesita para sostenerse.

    Es la contracara de slope_limit: en vez de bajar lo que esta muy parado,
    ENSANCHA su base. Cada pico se reconstruye como un cono que baja un escalon
    cada band_px pixeles, y se queda el maximo contra el target.

    Hace falta porque el heightmap viejo tiene las Montanas Ardientes pintadas
    como manchas angostas apoyadas directo sobre la meseta de tierra: sin
    faldon, slope_limit las aplasta a colinas --probado: el maximo del borrador
    daba 4 y nada mas que un 0.4% del mapa-- que es tecnicamente correcto pero
    deja el mapa sin cordillera. Con faldon la cordillera sobrevive, y ademas
    el faldon ES la banda de colinas que hay que pintar a mano para que la
    montana se funda con la llanura: esto la propone sola.

    El cono se confina a la tierra para que no cruce la costa.
    """
    f = np.where(land, target.astype(np.float64), 0.0)
    step = 1.0 / float(band_px)
    for _ in range(int(target.max() * band_px) + 2):
        nf = np.where(land, np.maximum(f, ndi.grey_dilation(f, footprint=EIGHT) - step), 0.0)
        if np.array_equal(nf, f):
            break
        f = nf
    return f


def slope_limit(field, sea, band_px):
    """La funcion mas grande que es <= field y sube como mucho un escalon cada
    band_px pixeles.

    Donde habia un salto de 200 niveles en un pixel aparecen solas las bandas
    intermedias. Y garantiza que el validador pase: el piso de una funcion
    (1/band)-Lipschitz cambia como mucho en 1 entre vecinos, asi que no puede
    quedar un salto de nivel.

    El mar entra como condicion de borde en 1.0, no en 0.0: si entrara en cero,
    la tierra pegada a la costa quedaria en 1/band, el piso daria 0 y la erosion
    se comeria la linea de costa.
    """
    f = np.where(sea, 1.0, field.astype(np.float64))
    step = 1.0 / float(band_px)
    for _ in range(int(f.max() * band_px) + 2):
        nf = np.minimum(f, ndi.grey_erosion(f, footprint=EIGHT) + step)
        if np.array_equal(nf, f):
            break
        f = nf
    out = np.floor(f + 1e-9).astype(np.int8)
    out = np.maximum(out, 1)
    out[sea] = 0
    return out


def report_dropped(g, land, cut=TRACE_SEA_CUT):
    """Lista lo que el umbral del borrador manda al mar.

    Son pixeles que el heightmap de origen tiene pintados --gris > 0-- pero por
    debajo de cut, asi que el borrador los convierte en oceano. El script no los
    puede distinguir de ruido de compresion, pero quien dibujo si: por eso se
    listan con su posicion en porcentaje de la imagen, para ir a mirarlos sobre
    la acuarela con el overlay al lado.
    """
    drawn = ndi.binary_fill_holes(
        ndi.binary_closing(g > 0.5, np.ones((5, 5), bool)))
    drawn[0, :] = drawn[-1, :] = drawn[:, 0] = drawn[:, -1] = False
    lost = drawn & ~land
    if not lost.any():
        print('  el umbral de mar (%.1f) no descarto nada pintado.' % cut)
        return 0

    h, w = g.shape
    lab, n = ndi.label(lost, EIGHT)
    sizes = np.bincount(lab.ravel())
    sizes[0] = 0
    print('  el umbral de mar (%.1f) mando al oceano %d px pintados, en %d '
          'componentes.' % (cut, int(lost.sum()), n))
    print('  Son tierra del dibujo que el borrador NO va a proponer como tierra.'
          '\n  Los mas grandes, para ir a mirarlos sobre tools/map-tiers-draft-overlay.png:')
    for i in np.argsort(sizes)[::-1][:8]:
        if sizes[i] == 0:
            break
        ys, xs = np.where(lab == i)
        print('    %6d px   x %3.0f%%..%3.0f%%   y %3.0f%%..%3.0f%%'
              % (sizes[i], 100.0 * xs.min() / w, 100.0 * xs.max() / w,
                 100.0 * ys.min() / h, 100.0 * ys.max() / h))
    return int(lost.sum())


def trace(band_px=TRACE_BAND_PX, src_png=None):
    """Arma tools/map-tiers-draft.png a partir del heightmap pintado a mano.

    La fuente es, por defecto, el map-height.png que ya existe. OJO: una vez
    que se genero el heightmap nuevo, ese archivo YA NO es el pintado a mano, y
    volver a trazar bootstrapea del mapa generado en vez de del dibujo. Para
    volver al original:

        git show HEAD:assets/img/map-height.png > tools/old-height.png
        python tools/make_heightmap.py --trace --trace-src tools/old-height.png

    No se usan los colores de la acuarela:
    la acuarela tiene el mar en rgb(187,182,189) y la llanura de Carnahan en
    rgb(170,163,146) --se pisan-- mientras que el heightmap ya codifica la
    intencion de altura que se dibujo a mano. El borrador la PORTA al formato
    nuevo; lo que queda para la mano es la costa, que es justo lo que hay que
    redibujar a 1252x900 para que siga la linea de tinta.
    """
    src_png = src_png or HEIGHT_PNG
    if not os.path.exists(src_png):
        die('no esta %s, que es de donde sale el borrador.' % src_png)
    src = Image.open(src_png).convert('L')
    w, h = (Image.open(WATERCOLOR).size if os.path.exists(WATERCOLOR)
            else (src.width * 2, src.height * 2))
    print('borrador: %s (%dx%d) -> %dx%d' % (short(src_png),
                                             src.width, src.height, w, h))

    # Bilineal y despues umbral, en vez de vecino mas cercano: la costa sale
    # bastante menos poligonal ya de entrada.
    g = np.asarray(src.resize((w, h), Image.Resampling.BILINEAR), np.float64)
    land = g > TRACE_SEA_CUT

    land = ndi.binary_closing(land, np.ones((5, 5), bool))
    land = ndi.binary_fill_holes(land)
    land[0, :] = land[-1, :] = land[:, 0] = land[:, -1] = False

    report_dropped(g, land)

    # El Borde y La Grieta estan dibujados con trama punteada, y los puntos
    # oscuros de la trama caen abajo del primer corte: sin esto el borrador
    # llena ese sector de parches a nivel del mar --que es literalmente el
    # issue #61, "la grieta deberia estar por encima del nivel del mar"--. La
    # trama es textura, no altura, asi que se promedia antes de cortar. Las
    # cumbres que el promedio achate las vuelve a levantar grow_apron.
    g = np.where(land, ndi.gaussian_filter(g, 5.0), g)

    # Cortes sacados del histograma real del heightmap viejo: el mar en 0, la
    # meseta de tierra en 41, las sierras en 56/71 y las cumbres hasta 245.
    cuts = [8, 32, 50, 85, 130, 190]
    target = np.digitize(g, cuts).astype(np.int8)   # 0..6
    target[~land] = 0
    target = np.maximum(target, land.astype(np.int8))

    grown = grow_apron(target, land, band_px)
    tier = slope_limit(grown, ~land, band_px)

    # La plataforma es una banda COSTERA por definicion: esta al nivel del mar,
    # y tierra adentro eso se ve como una laguna. El heightmap viejo dejaba los
    # valles de El Borde ahi abajo --issue #61, "la grieta deberia estar por
    # encima del nivel del mar"-- asi que lo que no toca la costa sube un
    # escalon. Subir nunca crea un salto de nivel: los vecinos ya eran >= 1.
    d_sea = ndi.distance_transform_edt(land)
    tier[(tier == 1) & (d_sea > band_px)] = 2
    tier, specks = despeckle(tier)
    for t, n, px in specks:
        print('  despeckle: %d componentes sueltos del escalon %d (%s), %d px'
              % (n, t, NAMES[t], px))

    Image.fromarray(tier_to_rgb(tier)).save(DRAFT_PNG)
    print('  escrito %s' % os.path.relpath(DRAFT_PNG, ROOT))
    hist = np.bincount(tier.ravel(), minlength=len(PALETTE))
    for t, c in enumerate(hist):
        if c:
            print('    %d %-12s %7d px  %5.2f%%' % (t, NAMES[t], c, 100 * c / tier.size))
    bad = validate(tier)
    print('  validacion del borrador: %s'
          % ('OK' if not bad else '\n    ' + '\n    '.join(bad)))
    comp = debug_composite(tier, os.path.join(HERE, 'map-tiers-draft-overlay.png'))
    if comp:
        print('  superposicion sobre la acuarela: %s' % os.path.relpath(comp, ROOT))
    print('\nAhora: abrir el borrador en el editor con assets/img/map.jpg debajo,\n'
          'CORREGIR LA COSTA --que es lo que el borrador no puede saber-- y las\n'
          'bandas, guardarlo como tools/map-tiers.png y correr\n'
          '  python tools/make_heightmap.py --report\n'
          '\nEl borrador sin esa pasada deja la costa donde la dejo el umbral, no\n'
          'donde esta la linea de tinta.\n')


# ---------------------------------------------------------------------------
# El nivel del mar, del otro lado
# ---------------------------------------------------------------------------

# SEA_LEVEL sale de H[1] y queda horneado en el PNG, pero la ALTURA DEL PLANO DE
# AGUA la saca el sitio de map_3d_sea en _config.yml. Era el unico salto del
# camino que se copiaba a mano, y es invisible cuando se rompe: no hay error en
# ningun lado, simplemente se hunde el mapa. Asi que lo verifica el script.
#
# El numero se captura con \d+(\.\d+)? y no con [0-9.]+ para que un "0.2.5" no
# pase el regex y despues reviente el float().
CONFIG_KEY = 'map_3d_sea'
CONFIG_RE = re.compile(r'^(' + CONFIG_KEY + r':[ \t]*)(\d+(?:\.\d+)?)[ \t]*$',
                       re.MULTILINE)


def check_config(write=False, path=CONFIG_YML):
    """Verifica --y con write, corrige-- map_3d_sea en _config.yml.

    Con regex y no con pyyaml a proposito: requirements.txt tiene tres paquetes
    y no hace falta un cuarto para leer un escalar. Reescribir con pyyaml,
    ademas, tiraria todos los comentarios del archivo, que aca son la
    documentacion.

    Devuelve True si el sitio y el heightmap estan de acuerdo.
    """
    rel = os.path.relpath(path, ROOT)
    want = '%.3f' % SEA_LEVEL

    if not os.path.exists(path):
        print('\nno esta %s: no se pudo verificar %s.' % (rel, CONFIG_KEY))
        return False

    # newline='' en los dos lados: sin esto la lectura traduce los fines de
    # linea y la escritura los aplana, y un --write-config reescribiria el
    # archivo entero en vez de un numero.
    with open(path, 'r', encoding='utf-8', newline='') as fh:
        src = fh.read()

    m = CONFIG_RE.search(src)
    if m is None:
        print('\n%s NO TIENE LA CLAVE %s.\n'
              '  El plano de agua va a caer en el default del include en vez de\n'
              '  en el nivel del mar de este heightmap. Agregar:\n'
              '      %s: %s' % (rel, CONFIG_KEY, CONFIG_KEY, want))
        return False

    have = float(m.group(2))
    if abs(have - SEA_LEVEL) < 1e-9:
        print('\n%s:  %s: %s  coincide con H[1].' % (rel, CONFIG_KEY, m.group(2)))
        return True

    if write:
        src = src[:m.start()] + m.group(1) + want + src[m.end():]
        with open(path, 'w', encoding='utf-8', newline='') as fh:
            fh.write(src)
        print('\n%s:  %s  %s -> %s  (reescrito)'
              % (rel, CONFIG_KEY, m.group(2), want))
        return True

    print('\nEL NIVEL DEL MAR NO COINCIDE.\n'
          '  este heightmap:   H[1] = %s\n'
          '  %-17s %s: %s\n'
          '\n'
          '  Asi publicado, el plano de agua no cae donde cae la costa del\n'
          '  dibujo, y el mapa se ve hundido o inundado sin que falle nada.\n'
          '  Arreglar con:\n'
          '      python tools/make_heightmap.py --write-config'
          % (want, rel + ':', CONFIG_KEY, m.group(2)))
    return False


# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    ap.add_argument('--trace', action='store_true',
                    help='arma un borrador de mascara desde el heightmap actual')
    ap.add_argument('--trace-src', metavar='PNG', default=None,
                    help='heightmap del que sale el borrador (por defecto, el publicado)')
    ap.add_argument('--check', action='store_true',
                    help='solo valida tools/map-tiers.png')
    ap.add_argument('--report', action='store_true',
                    help='genera e imprime el diagnostico, con imagenes de debug')
    ap.add_argument('--allow-skips', action='store_true',
                    help='genera igual aunque haya saltos de nivel (no recomendado)')
    ap.add_argument('--blur', type=float, default=BLUR_PX)
    ap.add_argument('--relief', type=float, default=0.12,
                    help='map_3d_relief, solo para calcular la pendiente del reporte')
    ap.add_argument('--out', default=HEIGHT_PNG)
    ap.add_argument('--write-config', action='store_true',
                    help='corrige map_3d_sea en _config.yml en vez de solo avisar')
    args = ap.parse_args()

    if args.trace:
        trace(src_png=args.trace_src)
        return

    if not os.path.exists(TIERS_PNG):
        die('no esta %s.\n'
            '  Para arrancar:  python tools/make_heightmap.py --trace'
            % os.path.relpath(TIERS_PNG, ROOT))

    tier = read_tiers(TIERS_PNG)
    print('mascara %s  %dx%d' % (os.path.relpath(TIERS_PNG, ROOT),
                                 tier.shape[1], tier.shape[0]))

    tier, specks = despeckle(tier)
    for t, n, px in specks:
        print('  despeckle: %d componentes sueltos del escalon %d (%s), %d px'
              % (n, t, NAMES[t], px))
        if px > tier.size * 0.001:
            print('    ^ son muchos. Sintoma clasico de guardar la mascara como '
                  'JPEG o con antialiasing.')

    problems = validate(tier, os.path.join(HERE, 'map-tiers-problemas.png'))
    if problems:
        head = 'la mascara tiene problemas:\n  - ' + '\n  - '.join(problems)
        if args.check or not args.allow_skips:
            die(head + '\n\n  Con --allow-skips se genera igual, pero van a salir '
                       'acantilados.')
        print(head)
    elif args.check:
        print('validacion: OK')
        # --check valida el par completo: la mascara Y el nivel del mar con
        # el que el sitio la va a leer. Una mascara impecable publicada con
        # un map_3d_sea equivocado se ve igual de mal que una rota.
        if not check_config(write=args.write_config):
            sys.exit(1)
        return

    h, _ = build_height(tier, verbose=args.report)
    field, repaired = finish(h, tier, blur_px=args.blur)

    tier_small = np.asarray(
        Image.fromarray(tier.astype(np.uint8)).resize(
            (field.shape[1], field.shape[0]), Image.Resampling.NEAREST), np.int8)

    src_hash = hashlib.sha256(open(TIERS_PNG, 'rb').read()).hexdigest()[:16]
    arr = write_gray_png(args.out, field, {
        'Software': 'tools/make_heightmap.py',
        'Source': 'tools/map-tiers.png sha256:' + src_hash,
        'Palette': ';'.join('%02X%02X%02X' % c for c in PALETTE),
        'Heights': ';'.join('%.3f' % v for v in H),
        'SeaLevel': '%.3f' % SEA_LEVEL,
        'BowlSpanPx': str(BOWL_SPAN_PX),
        'BlurPx': '%.2f' % args.blur,
    })
    print('escrito %s  %dx%d, gris de 8 bits sin alfa, %d bytes'
          % (os.path.relpath(args.out, ROOT), arr.shape[1], arr.shape[0],
             os.path.getsize(args.out)))
    if repaired:
        print('  reparacion de orilla: %d px a resolucion plena (%.3f%%)'
              % (repaired, 100.0 * repaired / h.size))

    if args.report:
        below = report(field, tier_small, relief=args.relief)
        comp = debug_composite(tier, os.path.join(HERE, 'map-tiers-overlay.png'))
        if comp:
            print('superposicion sobre la acuarela: %s'
                  % os.path.relpath(comp, ROOT))
        if below:
            sys.exit(1)

    # Antes esto solo IMPRIMIA el valor para copiar a mano. Imprimir no es
    # un contrato: el salto se rompio en silencio una vez y se hundio el
    # mapa entero. Ahora se verifica, y falla.
    if not check_config(write=args.write_config):
        sys.exit(1)
    print('')


if __name__ == '__main__':
    main()
