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

El nivel del mar es ESTRUCTURAL, no un recorte: SEA_LEVEL == H[LAND_TIER], el
piso del primer escalon de tierra. La tierra queda >= SEA_LEVEL por
construccion, asi que el bug de la tierra hundida no es algo que haya que
vigilar: es irrepresentable.

La UNICA excepcion es deliberada y se pinta con un color propio: la grieta
seca, una region tierra adentro que baja muy por debajo del nivel del mar y que
el visor no inunda. No es un escalon --no puede serlo, ver el comentario de
GRIETA_RGB-- sino un recorte que se aplica despues, y que queda excluido
del invariante a proposito y se informa aparte en --report. El assert que hay mas abajo esta para cazar errores de este
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

    python tools/make_heightmap.py --upgrade   # migra una mascara de 7 colores
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
WATER_PNG  = os.path.join(ROOT, 'assets', 'img', 'map-water.png')
CONFIG_YML = os.path.join(ROOT, '_config.yml')

# ---------------------------------------------------------------------------
# La paleta y la tabla de alturas. Esto es DATO DE ARTE: es lo que se toca
# cuando el relieve no se ve bien, y es casi lo unico que hay que tocar.
# ---------------------------------------------------------------------------

# Colores lo mas separados posible entre si, a proposito: la mascara se snapea
# al color de paleta mas cercano en RGB, y dos verdes parecidos se
# intercambiarian solo con que el balde deje un borde suavizado.
PALETTE = [
    (0x00, 0xFF, 0xFF),   # 0 fosa abisal
    (0x00, 0x00, 0x00),   # 1 mar / plataforma continental
    (0x00, 0x00, 0xFF),   # 2 playa  <-- su piso ES el nivel del mar
    (0x00, 0xFF, 0x00),   # 3 tierra baja
    (0x80, 0xFF, 0x00),   # 4 vega
    (0xFF, 0xFF, 0x00),   # 5 llanura
    (0xFF, 0x80, 0x00),   # 6 colinas
    (0xFF, 0x00, 0x00),   # 7 montanas
    (0xFF, 0x00, 0xFF),   # 8 alta montana
    (0xFF, 0xFF, 0xFF),   # 9 cumbres
]

NAMES = ['fosa abisal', 'mar', 'playa', 'tierra baja', 'vega',
         'llanura', 'colinas', 'montanas', 'alta montana', 'cumbres']

# El indice del escalon NO vive en el PNG, vive en el orden de esta lista. Por
# eso agregar la fosa adelante corre todos los indices sin obligar a repintar
# nada: el negro sigue queriendo decir "mar", el azul sigue siendo la playa.
#
# El peor par de la paleta ya estaba a distancia 128 (amarillo-naranja), y los
# tres colores nuevos no bajan de 127 contra ninguno: lima esta a 127 del
# amarillo, magenta a 255 de todo, cian a 255 del azul. SNAP_TOLERANCE = 60
# sigue siendo menos que la mitad de 127, asi que un pixel ambiguo sigue siendo
# un ERROR y no un snapeo silencioso al vecino equivocado.

SEA_TIER  = 1                 # ultimo escalon que es agua
LAND_TIER = SEA_TIER + 1      # primer escalon que es tierra; su piso es el mar

# ---------------------------------------------------------------------------
# La grieta seca: un recorte, NO un peldano
# ---------------------------------------------------------------------------
#
# Una region tierra adentro que esta muy por debajo del nivel del mar y que no
# se inunda. No se puede expresar con un escalon mas, y vale la pena saber por
# que, porque es lo que explica que esto sea un mecanismo aparte:
#
# La escalera es MONOTONA en altura --el escalon t ocupa [H[t], H[t+1]]-- y la
# regla de no-saltar obliga a recorrerla de forma continua EN EL ESPACIO. Una
# grieta rodeada de tierra alta tendria que bajar pasando por todos los
# escalones intermedios; si su piso esta bajo el nivel del mar, esos escalones
# intermedios tambien lo estan, y todo escalon por debajo de LAND_TIER es MAR.
# O sea: para pintarla habria que pintar mar tierra adentro, que es un lago.
# Y al reves: un escalon seco bajo el mar tendria que ir entre el mar y la
# playa en la escalera, y entonces la regla de no-saltar obligaria a pintarlo
# como una banda a lo largo de TODA la costa.
#
# Asi que la grieta no entra en la escalera. Se pinta con su propio color,
# se reemplaza por el escalon que la rodea ANTES de validar --asi el resto del
# pipeline ni se entera-- y despues se hunde su region con la misma maquinaria
# de siempre: transformada de distancia + smoothstep. Ver carve_grieta().
#
# El plano de agua del visor taparia igual todo lo que quede abajo del nivel
# del mar, asi que el script ademas emite assets/img/map-water.png, la mascara
# que le agujerea el agua justo ahi. Sin esa mascara la grieta se ve como un
# lago profundo, que es exactamente lo que no es.
GRIETA_RGB  = (0x80, 0x40, 0x00)
GRIETA_NAME = 'grieta seca'

# Gris con el que validate() marca los saltos de nivel. Antes era magenta, que
# ahora es un color de la paleta: el marcador tiene que ser un color que NO
# este en la paleta, o no se distingue de un escalon.
JUMP_MARK = (0x80, 0x80, 0x80)

# La paleta vieja, de siete colores, y a que escalon nuevo va cada uno. Solo la
# usa --upgrade, para migrar una mascara pintada antes de que existieran la
# fosa, la vega y la alta montana.
LEGACY_PALETTE = [
    (0x00, 0x00, 0x00), (0x00, 0x00, 0xFF), (0x00, 0xFF, 0x00),
    (0xFF, 0xFF, 0x00), (0xFF, 0x80, 0x00), (0xFF, 0x00, 0x00),
    (0xFF, 0xFF, 0xFF),
]
LEGACY_MAP = [1, 2, 3, 5, 6, 7, 9]

# Ancho, en pixeles, de las bandas que --upgrade abre para los escalones que la
# paleta vieja no tenia. Angostas a proposito: ver upgrade().
UPGRADE_BAND_PX = 6

# H son alturas de BORDE, con len(PALETTE)+1 entradas: el escalon t ocupa la
# banda [H[t], H[t+1]]. Asi el escalon de arriba tiene pin superior y
# desaparece la pregunta de "a que apunta la cumbre". Es la clave del esquema.
#
# El espaciado es a proposito NO uniforme --apretado cerca del mar, ancho en la
# montana--. Escalones equiespaciados mas el smoothstep, que tiene pendiente
# cero en cada contorno, se leen como una torta de casamiento.
H = [
    0.00,   # piso de la fosa abisal
    0.22,   # techo de la fosa / piso del mar
    0.40,   # <-- NIVEL DEL MAR. piso de la playa, techo del mar
    0.44,   # +0.04  playa: casi plana, para que la costa se tienda
    0.50,   # +0.06  tierra baja
    0.57,   # +0.07  vega
    0.65,   # +0.08  llanura
    0.75,   # +0.10  colinas
    0.86,   # +0.11  montanas
    0.95,   # +0.09  alta montana
    1.00,   # +0.05  techo de las cumbres
]
# Los pasos de tierra crecen hacia arriba (0.04, 0.06, 0.07, 0.08, 0.10, 0.11)
# y se achican en el ultimo tramo: la costa sale tendida, la ladera se va
# parando, y la cumbre vuelve a juntarse. Es como se lee un continente.
#
# EL REPARTO DEL RANGO. El gris 0..1 es un presupuesto fijo y el nivel del mar
# es donde se parte:
#
#     agua   0.00 -> 0.40   (antes 0.25)   +60% de profundidad
#     tierra 0.40 -> 1.00   (antes 0.57)   +5%  de altura
#
# El techo era 0.82 y sobraba un 18% del rango sin usar. Ahora se usa entero, y
# eso es lo que paga la fosa abisal sin achatar la tierra. map_3d_relief no
# cambia: la montana sigue midiendo lo mismo contra la llanura.
#
# Con diez escalones en vez de siete el paso mas grande baja de 0.14 a 0.11,
# asi que con el mismo ancho de banda las laderas salen MAS TENDIDAS que antes.
# La verticalidad extra no viene de pendientes mas paradas --eso se lee como
# pared-- sino de tener mas escalones y mas rango para repartir.

SEA_LEVEL = H[LAND_TIER]

# A donde baja el piso de la grieta, y en cuantos pixeles cae. Es altura
# ABSOLUTA, no una resta: el borde empalma con el terreno que la rodea y el
# fondo llega aca.
#
# 0.00 es el piso del rango: mas abajo no existe. Es lo que pide La Grieta, que
# segun lore/planos_taphaestri.md da a los nueve infiernos y al abismo. Queda
# tan honda como la fosa abisal del oceano --o sea que el mar deja de ser el
# punto mas bajo del mundo--; si alguna vez se quiere que la fosa gane, con
# subir esto a 0.04 alcanza.
GRIETA_FLOOR = 0.00

# EL ESPESOR DE LA PARED, y es lo que distingue una grieta de una hondonada.
#
# La primera version de esto repartia la bajada a lo largo de GRIETA_SPAN_PX
# contados desde el borde hacia adentro, igual que DOME_SPAN_PX con los picos.
# Para una cuenca esta bien. Para una falla es inservible, porque ata la
# PROFUNDIDAD al ANCHO: medido con span 60, una grieta de 20 px de ancho
# quedaba en 0.421 --por ENCIMA del nivel del mar-- y habia que pintarla de
# 120 px, el 10% del continente, para que tocara el piso. Eso no es una falla,
# es un canon.
#
# Aca la caida ocupa los primeros GRIETA_WALL_PX pixeles y despues el piso es
# plano. La profundidad deja de depender del ancho: una grieta de 20 px y una
# de 200 llegan las dos al fondo, y el ancho pasa a gobernar solo cuanto se ve.
# Con 4 px la caida de ~0.44 ocurre en 1.2 celdas de malla: ~87 grados, una
# pared. Que es exactamente lo que tiene que ser.
GRIETA_WALL_PX = 4

# Un componente mas chico que esto no es una falla, es un borron del pincel.
#
# Con el perfil viejo una mancha chica se hundia poco y no hacia dano. Con
# este, CUALQUIER cosa de mas de 2*GRIETA_WALL_PX de ancho cae entera al fondo,
# asi que un descuido del balde abre un agujero al infierno. MIN_COMPONENT_PX,
# que son 8 px, es demasiado permisivo para algo tan destructivo.
GRIETA_MIN_PX = 64

# Ancho minimo, en pixeles, para que la grieta SOBREVIVA a la resolucion.
#
# La profundidad ya no depende del ancho, pero el desenfoque de finish() si se
# come el piso de un tajo angosto. Medido sobre la mascara real, con el piso en
# 0.00 y el labio en ~0.44:
#
#     ancho   piso que queda   profundidad que sobrevive
#       10        0.181                 59%
#       14        0.083                 81%
#       16        0.053                 88%
#       20        0.018                 96%
#       30        0.000                100%
#
# O sea: 20 px y la grieta llega practicamente al fondo, 30 y llega exacto.
# Abajo de 16 el tajo se nota relleno y no hay constante que lo arregle --hay
# que pintar mas ancho-- asi que el script avisa en vez de dejarlo pasar.
GRIETA_THIN_PX = 16

# Ancho del collar alrededor de la grieta. Tiene que ser mayor que BLUR_PX,
# porque es justo el alcance con el que el desenfoque de finish() arrastra para
# abajo el terreno de alrededor. Ver grieta_zone().
#
# Son 8 y no 6 porque el salto crecio: con el piso en 0.00 la caida es de 0.44
# y no de 0.26, y el tiron del desenfoque crece con ella. A 6 px del labio el
# terreno quedaba en 0.411, a un pelo de 0.400 y de que la reparacion de orilla
# le dejara una repisa plana alrededor del tajo.
GRIETA_RIM_PX = 8

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

# Espesor maximo, en pixeles, de una franja fuera de paleta que el script
# repara solo en vez de rechazar.
#
# El antialiasing de un borde es una franja de UN pixel: el editor mezcla los
# dos colores que tiene a los costados, y la mezcla de dos colores lo mas
# separados posible cae lejos de los dos --el negro con el cian dan #007C7C, a
# 175 de ambos--. Rechazar eso es correcto en espiritu y carisimo en la
# practica: obliga a repintar bordes a mano por algo que no cambia nada, porque
# reasignar esa franja al color confiable mas cercano mueve el borde medio
# pixel y se acabo.
#
# Lo que NO se repara es una REGION pintada de un color que no esta en la
# paleta, y el espesor es justo lo que las distingue: una franja de
# antialiasing nunca pasa de 1 o 2 px, un balde mal elegido tiene cuerpo.
AA_FRINGE_PX = 2

# Un color que NO es de la paleta pero que entra dentro de SNAP_TOLERANCE se
# snapea en silencio, y ahi hay una trampa que ya mordio una vez: una region de
# 8104 px pintada en #FF5E00 --a 34 del naranja-- se iba a convertir en colinas
# sin que nada avisara, y con eso la cordillera entera se aplanaba, porque lo
# que en realidad era es montanas (#FF0000, a 94). El snapeo silencioso es
# justo lo que se quiere para un borde; para una mancha con cuerpo es un bug
# invisible. Asi que se avisa cuando una de esas manchas tiene espesor y peso.
SILENT_SNAP_PX = 200

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

def snap(path, palette):
    """Abre una mascara y devuelve el indice del color de paleta mas cercano.

    Acepta cualquier modo de color: todo se pasa a RGB y se snapea al color de
    paleta mas cercano. Una mascara indexada que el editor reordeno, un borde
    suavizado o un balde un poco corrido se resuelven solos; un color que no
    esta en la paleta es un ERROR, no un snapeo silencioso.

    Toma la paleta por parametro porque --upgrade lee la mascara vieja, de
    siete colores, con exactamente el mismo cuidado.
    """
    im = Image.open(path)
    if im.mode == 'P':
        im = im.convert('RGBA')
    rgb = np.asarray(im.convert('RGB')).astype(np.int32)

    pal = np.asarray(palette, np.int32)                      # (P, 3)
    d2 = ((rgb[:, :, None, :] - pal[None, None, :, :]) ** 2).sum(-1)
    idx = d2.argmin(-1)
    worst = np.sqrt(d2.min(-1))

    bad = worst > SNAP_TOLERANCE
    if bad.any():
        if bad.all():
            die('ni un solo pixel de %s esta en la paleta.' % short(path))
        thick = float(ndi.distance_transform_edt(bad).max())
        if thick > AA_FRINGE_PX:
            # Hay cuerpo: no es un borde suavizado, es un color mal elegido.
            # Se nombra el componente mas gordo, que es el que hay que ir a ver.
            lab, n = ndi.label(bad, structure=EIGHT)
            sizes = np.bincount(lab.ravel(), minlength=n + 1)
            big = int(sizes[1:].argmax()) + 1
            ys, xs = np.nonzero(lab == big)
            c = rgb[ys[0], xs[0]]
            die('%d pixeles con un color que no esta en la paleta '
                '(distancia > %d).\n'
                '  La mancha mas grande son %d px de #%02X%02X%02X, alrededor '
                'de (%d,%d),\n  y tiene %.0f px de espesor: eso no es un borde '
                'suavizado, es un balde\n  con el color equivocado. Corregirlo '
                'a un color de la paleta.\n'
                '  (Una franja de hasta %d px el script la repara solo.)'
                % (bad.sum(), SNAP_TOLERANCE, int(sizes[big]), c[0], c[1], c[2],
                   int(xs[0]), int(ys[0]), thick, AA_FRINGE_PX))

        # Franja fina: antialiasing. Cada pixel ambiguo toma el color del pixel
        # CONFIABLE mas cercano. Es la misma transformada de distancia que usa
        # despeckle(), y mueve el borde medio pixel.
        fill = ndi.distance_transform_edt(bad, return_indices=True)[1]
        idx = idx[fill[0], fill[1]]
        print('  antialiasing: %d px fuera de paleta en una franja de %.0f px, '
              'reasignados\n    al color de paleta confiable mas cercano.'
              % (int(bad.sum()), thick))

    # Snapeo silencioso con cuerpo: ver SILENT_SNAP_PX.
    exact = np.zeros(rgb.shape[:2], bool)
    for t in palette:
        exact |= ((rgb[:, :, 0] == t[0]) & (rgb[:, :, 1] == t[1])
                  & (rgb[:, :, 2] == t[2]))
    off = ~exact & ~bad
    if off.any():
        lab, n = ndi.label(off, structure=EIGHT)
        sizes = np.bincount(lab.ravel(), minlength=n + 1)
        mx = np.atleast_1d(ndi.maximum(ndi.distance_transform_edt(off), lab,
                                       np.arange(1, n + 1)))
        for i in range(n):
            if mx[i] > AA_FRINGE_PX and sizes[i + 1] >= SILENT_SNAP_PX:
                ys, xs = np.nonzero(lab == i + 1)
                c = rgb[ys[0], xs[0]]
                t = palette[idx[ys[0], xs[0]]]
                print('  aviso: %d px de #%02X%02X%02X, que no es un color de la '
                      'paleta, se van a\n    tomar como #%02X%02X%02X (%s). '
                      'Si no era eso, es un escalon entero mal\n    pintado y no '
                      'se va a notar en ningun lado. Alrededor de (%d,%d).'
                      % (int(sizes[i + 1]), c[0], c[1], c[2], t[0], t[1], t[2],
                         NAMES[idx[ys[0], xs[0]]]
                         if idx[ys[0], xs[0]] < len(NAMES) else GRIETA_NAME,
                         int(xs[0]), int(ys[0])))
    return idx


def read_tiers(path):
    """Lee la mascara y devuelve (escalones int8, mascara de grieta bool).

    La grieta se saca de la escalera ACA, en la puerta de entrada: sus
    pixeles se reemplazan por el escalon del vecino mas cercano, asi que de
    read_tiers para adentro `tier` es una escalera monotona comun y corriente y
    el resto del pipeline --validacion, no-saltar, EDT, cuenca, domo-- no
    necesita saber que la grieta existe. Se vuelve a aplicar al final, sobre
    el campo ya construido, en carve_grieta().
    """
    idx = snap(path, list(PALETTE) + [GRIETA_RGB])

    # raw son TODOS los pixeles marrones; grieta son los que sobreviven al
    # despeckle. La diferencia importa y costo un bug: el 0 de abajo es un
    # relleno provisorio, pero 0 tambien es un escalon de verdad --la fosa
    # abisal, el punto mas hondo del mapa-- asi que todo pixel marron tiene que
    # recibir despues su altura real. Si el relleno final se hiciera con
    # `grieta`, los pixeles de los componentes DESCARTADOS se quedarian en 0 y
    # una manchita de 14 px se convertiria en un pozo de oceano abisal en medio
    # de la llanura. Paso. Por eso el relleno se hace con `raw`.
    raw = idx == len(PALETTE)
    grieta = raw.copy()
    tier = np.where(raw, 0, idx).astype(np.int8)

    if raw.all():
        die('la mascara es toda grieta: no hay terreno con el que empalmar.')

    if grieta.any():
        # Una mancha marron suelta no tiene que abrir un agujero al infierno.
        # Umbral propio y mucho mas alto que MIN_COMPONENT_PX: ver GRIETA_MIN_PX.
        lab, n = ndi.label(grieta, structure=EIGHT)
        sizes = np.bincount(lab.ravel(), minlength=n + 1)
        keep = np.zeros(n + 1, bool)
        keep[1:] = sizes[1:] >= GRIETA_MIN_PX
        dropped = int((grieta & ~keep[lab]).sum())
        n_small = int((~keep[1:]).sum())
        grieta = keep[lab]
        if dropped:
            print('  despeckle: %d componentes de %s de menos de %d px '
                  '(%d px en total), descartados'
                  % (n_small, GRIETA_NAME, GRIETA_MIN_PX, dropped))

    if raw.any():
        # distance_transform_edt mide hasta el CERO mas cercano, o sea hasta el
        # pixel que NO es marron; return_indices da sus coordenadas. En los
        # pixeles que no son marron la distancia es 0 y el indice es el propio
        # pixel, asi que esto se puede aplicar al array entero.
        fill = ndi.distance_transform_edt(raw, return_indices=True)[1]
        tier = tier[fill[0], fill[1]]

    return tier, grieta


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


def validate(tier, debug_path=None, grieta=None):
    """Devuelve la lista de problemas. Vacia = la mascara sirve."""
    problems = []

    # 1. El anillo exterior tiene que ser mar. El plano de agua mide
    #    MAP_W * 1.6 (campaign_map_3d.html) y con un nivel del mar de verdad
    #    corta el borde del mapa: si ahi hay tierra se ve el canto de la malla,
    #    que no tiene faldon.
    border = np.concatenate([tier[0, :], tier[-1, :], tier[:, 0], tier[:, -1]])
    if (border > SEA_TIER).any():
        problems.append('el anillo exterior no es todo agua: %d pixeles del borde '
                        'tienen escalon > %d (%s)'
                        % (int((border > SEA_TIER).sum()), SEA_TIER, NAMES[SEA_TIER]))

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
            vis[ndi.binary_dilation(jump, np.ones((5, 5), bool))] = JUMP_MARK
            Image.fromarray(vis).save(debug_path)
            problems.append('se marcaron en gris en %s'
                            % os.path.relpath(debug_path, ROOT))

    # 4. La grieta es tierra hundida. Pegada al mar no es una grieta: es
    #    un agujero seco al lado del oceano, que el plano de agua agujereado
    #    deja ver como un tajo. Casi siempre es el balde que se escapo.
    if grieta is not None and grieta.any():
        if (grieta[0, :].any() or grieta[-1, :].any()
                or grieta[:, 0].any() or grieta[:, -1].any()):
            problems.append('la %s toca el borde de la imagen' % GRIETA_NAME)
        touching = grieta & ndi.binary_dilation(tier <= SEA_TIER, EIGHT)
        if touching.any():
            ys, xs = np.nonzero(touching)
            problems.append(
                'la %s toca el agua en %d pixeles (ej: (%d,%d)). Tiene que estar '
                'rodeada de tierra: es una grieta seca, no una bahia.'
                % (GRIETA_NAME, int(touching.sum()), int(xs[0]), int(ys[0])))

        # Esto NO es un problema que invalide la mascara --el heightmap sale
        # igual-- pero es la unica forma de enterarse de que el tajo se pinto
        # demasiado angosto y el desenfoque lo va a rellenar. Se avisa aca y no
        # en el reporte porque conviene saberlo ANTES de generar.
        thin = [w for w, _ in grieta_thin(grieta) if w < GRIETA_THIN_PX]
        if thin:
            print('  aviso: %d componentes de %s miden menos de %d px de ancho '
                  '(el mas angosto, %.0f px).\n'
                  '    El desenfoque les va a rellenar el piso: a 16 px sobrevive '
                  'el 88%% de la\n    profundidad, a 14 el 81%% y a 10 el 59%%. '
                  'Con 20 px llega al fondo.'
                  % (len(thin), GRIETA_NAME, GRIETA_THIN_PX, min(thin)))
    return problems


def tier_to_rgb(tier, grieta=None):
    pal = np.asarray(PALETTE, np.uint8)
    out = pal[np.clip(tier, 0, len(PALETTE) - 1)]
    if grieta is not None and grieta.any():
        out = out.copy()
        out[grieta] = GRIETA_RGB
    return out


def grieta_zone(grieta, px=GRIETA_RIM_PX):
    """La grieta mas un collar de px pixeles.

    Son dos cosas a la vez, y tienen que ser LA MISMA o aparece un escalon
    donde no hay nada:

      - donde el invariante del nivel del mar no aplica. El desenfoque de
        finish() es lineal y cruza el borde de la grieta, asi que arrastra
        para abajo una tira del terreno de alrededor. Si esa tira se "repara"
        subiendola al nivel del mar queda una repisa plana rodeando el pozo.
      - donde el visor no dibuja agua. Si el collar quedara fuera del agujero,
        esa misma tira hundida se veria inundada.
    """
    if not grieta.any():
        return grieta
    return ndi.binary_dilation(grieta, EIGHT, iterations=px)


# ---------------------------------------------------------------------------
# El generador
# ---------------------------------------------------------------------------

def build_height(tier, grieta=None, verbose=False):
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
    # dibujo. Si salta, el bug esta aca arriba, no en la mascara. La grieta
    # queda afuera porque su razon de ser es justamente violar esto, y se
    # excluye ANTES de hundirla para que el invariante siga valiendo para todo
    # el resto de la tierra.
    land = tier >= LAND_TIER
    if grieta is not None:
        land = land & ~grieta
    if land.any():
        lo = float(h[land].min())
        assert lo >= SEA_LEVEL - 1e-9, (
            'bug del generador: hay tierra en %.6f, debajo del nivel del mar %.3f'
            % (lo, SEA_LEVEL))

    if grieta is not None and grieta.any():
        h = carve_grieta(h, grieta)
    return h, kinds


def carve_grieta(h, grieta):
    """Abre el tajo: pared en los primeros GRIETA_WALL_PX px, piso plano.

    Los dos extremos del perfil son los que hacen que esto se vea bien, y los
    dos salen del mismo smoothstep:

      - En el borde --d = 0, w = 0-- la altura queda IDENTICA a la del terreno
        que la rodea, porque h ahi ya es la del escalon con el que read_tiers
        relleno el hueco. El empalme es continuo sin tener que ir a buscar la
        altura del labio: ya esta en h. Y smoothstep anula la derivada, asi que
        computeVertexNormals no dibuja un anillo de luz alrededor del tajo.
      - De GRIETA_WALL_PX para adentro --w = 1-- el piso es plano y la derivada
        tambien se anula. Por eso no hace falta normalizar por componente ni
        preocuparse por el eje medio: no hay cresta que aparezca en el medio de
        la grieta, que es el defecto clasico de hundir con una transformada de
        distancia.

    Entre esos dos extremos esta la pared, y es a proposito una pared: el
    reporte la va a medir en ~87 grados. Ver GRIETA_WALL_PX para por que el
    perfil es este y no el de una cuenca.
    """
    d = ndi.distance_transform_edt(grieta)
    w = smoothstep(np.clip(d / float(GRIETA_WALL_PX), 0.0, 1.0))
    return np.where(grieta, h + (GRIETA_FLOOR - h) * w, h)


def grieta_thin(grieta):
    """Ancho, en px, de la parte mas angosta de cada componente de grieta.

    El ancho de un componente en su punto mas angosto es 2 * (la distancia al
    borde mas grande que alcanza)... pero medida POR COMPONENTE, que es lo que
    hace el maximo de la transformada de distancia restringido a cada etiqueta.
    Un componente que nunca llega a GRIETA_THIN_PX/2 de distancia al borde es
    un tajo que el desenfoque va a rellenar.
    """
    if not grieta.any():
        return []
    d = ndi.distance_transform_edt(grieta)
    lab, n = ndi.label(grieta, structure=EIGHT)
    if n == 0:
        return []
    mx = np.atleast_1d(ndi.maximum(d, lab, np.arange(1, n + 1)))
    sz = np.bincount(lab.ravel(), minlength=n + 1)[1:]
    return [(float(2.0 * mx[i]), int(sz[i])) for i in range(n)]


def finish(h, tier, grieta=None, blur_px=BLUR_PX, out_size=(OUT_W, OUT_H)):
    """Desenfoque, reparacion de la orilla y bajada de resolucion."""
    blurred = ndi.gaussian_filter(h, blur_px) if blur_px > 0 else h

    # El desenfoque es lineal y cruza la orilla, donde el mar cae rapido: tira
    # para abajo una tira finita de playa. La garantia estructural ya hizo su
    # trabajo antes del blur; esto es una reparacion de uno o dos pixeles al
    # borde del agua, y se INFORMA, para que si alguna vez deja de ser
    # marginal se vea en el reporte en vez de quedar tapado.
    land = tier >= LAND_TIER
    if grieta is not None and grieta.any():
        land = land & ~grieta_zone(grieta)
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
        Image.fromarray(land.astype(np.uint8) * 255)
             .resize(out_size, Image.Resampling.NEAREST), np.uint8) > 127
    sunk2 = small_land & (small < SEA_LEVEL)
    repaired += int(sunk2.sum())
    small = np.where(sunk2, SEA_LEVEL, small)
    return np.clip(small, 0.0, 1.0), repaired


def build_water_mask(grieta, out_size=(OUT_W, OUT_H)):
    """Campo 0..1 para el plano de agua del visor: 1 = hay agua, 0 = no hay.

    Existe por una sola razon: el agua del mapa 3D es UN PLANO translucido que
    cubre todo, asi que sin esto cualquier cosa por debajo del nivel del mar se
    ve inundada, este donde este. La grieta seca seria un lago profundo.

    Lo unico que se agujerea es grieta_zone(): el resto queda en 1, asi que
    la costa del continente se dibuja exactamente igual que antes --la mascara
    no la toca ni la puede correr--. El canto del agujero cae sobre el collar,
    que es terreno por encima del nivel del mar, asi que no se ve.
    """
    m = np.ones(grieta.shape, np.float64)
    if grieta.any():
        m[grieta_zone(grieta)] = 0.0
        m = ndi.gaussian_filter(m, 2.0)

    # El anillo exterior tiene que quedar opaco. El plano de agua mide 1.6x el
    # mapa y la textura se estira hacia afuera con clamp-to-edge: si el borde
    # fuera transparente, desapareceria el agua de todo el exterior.
    m[0, :] = m[-1, :] = m[:, 0] = m[:, -1] = 1.0

    small = np.asarray(
        Image.fromarray(m.astype(np.float32), mode='F')
             .resize(out_size, Image.Resampling.BOX), np.float64)
    return np.clip(small, 0.0, 1.0)


# ---------------------------------------------------------------------------
# Diagnostico
# ---------------------------------------------------------------------------

def _mask_pairs(zone, shape):
    """Mascaras de los pares de vecinos que NO tocan zone, en x y en z.

    np.diff da un valor por PAR de pixeles, asi que para excluir una region hay
    que excluir todo par que la toque de alguno de los dos lados; si no, el
    escalon del borde se cuela igual. zone en None = no excluir nada.
    """
    if zone is None or not zone.any():
        return (np.ones((shape[0], shape[1] - 1), bool),
                np.ones((shape[0] - 1, shape[1]), bool))
    return (~(zone[:, :-1] | zone[:, 1:]), ~(zone[:-1, :] | zone[1:, :]))


def report(field, tier_small, grieta_small=None, zone_small=None,
           relief=0.12, seg_x=384):
    """Diagnostico del heightmap ya terminado.

    grieta_small es la grieta; zone_small es la grieta MAS su collar, o sea
    grieta_zone() bajado a resolucion. La diferencia importa: finish() deja
    deliberadamente el collar por debajo del nivel del mar --es el labio del
    tajo-- asi que si el reporte lo contara como tierra inundada, el test que
    tiene que dar 0 daria unos cientos de px y dejaria de servir. Es la misma
    zona que el visor destapa con la mascara de agua, asi que las tres cosas
    --el campo, el reporte y el agua-- miran exactamente el mismo conjunto.
    """
    if zone_small is None:
        zone_small = grieta_small
    arr = np.rint(field * 255).astype(np.int32)
    print('\n--- reporte -------------------------------------------------------')
    print('  salida            %d x %d, gris %d..%d'
          % (field.shape[1], field.shape[0], arr.min(), arr.max()))

    # El salto y la pendiente se miden SIN la grieta, por el mismo motivo: su
    # pared da ~80 grados y ~26 niveles siempre y a proposito, y taparia las
    # dos metricas que sirven para ver si el resto del mapa esta bien.
    out = _mask_pairs(zone_small, arr.shape)
    dxs, dzs = np.abs(np.diff(arr, axis=1)), np.abs(np.diff(arr, axis=0))
    step = max(int(dxs[out[0]].max(initial=0)), int(dzs[out[1]].max(initial=0)))
    print('  salto maximo entre pixeles vecinos   %d niveles  (antes: 164)%s'
          % (step, '   [sin la grieta]' if grieta_small is not None
             and grieta_small.any() else ''))

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

    # La pared de la grieta se mide aparte. Si entrara en este estadistico lo
    # tapa: da ~87 grados SIEMPRE y a proposito, asi que el numero dejaria de
    # servir para lo unico que sirve --ver el dia que una ladera de verdad se
    # para-- y el aviso de los 55 grados se volveria ruido de todos los runs.
    # Se dilata un par de celdas porque la pared cae entre dos vertices de la
    # malla, no sobre uno.
    gmesh = None
    if zone_small is not None and zone_small.any():
        gmesh = np.asarray(
            Image.fromarray(zone_small.astype(np.uint8) * 255)
                 .resize((seg_x + 1, seg_z + 1), Image.Resampling.NEAREST),
            np.uint8) > 127
        # La pared cae ENTRE dos vertices de la malla, no sobre uno, y el
        # NEAREST de arriba puede perderla: un par de celdas de margen.
        gmesh = ndi.binary_dilation(gmesh, EIGHT, iterations=2)

    keep_x, keep_z = _mask_pairs(gmesh, mesh.shape)

    vals = np.concatenate([gx[keep_x].ravel(), gz[keep_z].ravel()])
    slope = np.degrees(np.arctan(vals.max())) if vals.size else 0.0
    p999 = (np.degrees(np.arctan(np.percentile(vals, 99.9)))
            if vals.size else 0.0)
    wall = np.concatenate([gx[~keep_x].ravel(), gz[~keep_z].ravel()])
    wall_deg = np.degrees(np.arctan(wall.max())) if wall.size else 0.0

    print('  pendiente maxima en la malla         %.1f grados  (p99.9: %.1f)%s'
          % (slope, p999, '   [sin la grieta]' if gmesh is not None else ''))
    if slope > 55:
        print('    ^ arriba de ~55 el ojo lee "pared" en vez de "monte".')
        print('      Ensanchar la banda que este parada, no bajar su color.')

    land = tier_small >= LAND_TIER
    if zone_small is not None:
        land = land & ~zone_small
    below = int((land & (arr < round(SEA_LEVEL * 255))).sum())
    print('  nivel del mar                        %.3f  (gris %d)'
          % (SEA_LEVEL, round(SEA_LEVEL * 255)))
    print('  pixeles de tierra bajo el agua       %d   <-- tiene que ser 0  '
          '(antes: 569)' % below)

    # La grieta esta excluida del conteo de arriba a proposito, asi que se
    # informa aca: es la unica tierra que el mapa deja por debajo del agua, y
    # tiene que ser visible en el reporte y no un silencio.
    if grieta_small is not None and grieta_small.any():
        floor = float(field[grieta_small].min())
        print('  %-36s %d px, piso %.3f (%.3f bajo el mar)'
              % (GRIETA_NAME, int(grieta_small.sum()), floor, SEA_LEVEL - floor))
        if wall_deg:
            print('    pared ~%.0f grados en %d px   <-- es una pared a proposito'
                  % (wall_deg, GRIETA_WALL_PX))
        if floor > GRIETA_FLOOR + 0.02:
            print('    ^ el piso se quedo en %.3f en vez de %.3f: el desenfoque '
                  'relleno el tajo.\n'
                  '      No es la profundidad, es el ANCHO. Pintarla de al menos '
                  '%d px.' % (floor, GRIETA_FLOOR, GRIETA_THIN_PX))
    print('-------------------------------------------------------------------\n')
    return below


def debug_composite(tier, path, grieta=None):
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

    # La grieta entra como una region mas, para que su contorno tambien se
    # vea contra la acuarela: es justo lo que hay que verificar a ojo.
    lbl = np.where(grieta, len(PALETTE), tier) if grieta is not None else tier
    edges = np.zeros(tier.shape, bool)
    for dy, dx in ((0, 1), (1, 0)):
        sh = np.roll(np.roll(lbl, dy, 0), dx, 1)
        edges |= sh != lbl
    coast = edges & ndi.binary_dilation(tier <= SEA_TIER, EIGHT) & (tier >= LAND_TIER)

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

    El mar entra como condicion de borde en LAND_TIER, no en 0: si entrara en
    cero, la tierra pegada a la costa quedaria en 1/band, el piso daria 0 y la
    erosion se comeria la linea de costa.
    """
    f = np.where(sea, float(LAND_TIER), field.astype(np.float64))
    step = 1.0 / float(band_px)
    for _ in range(int(f.max() * band_px) + 2):
        nf = np.minimum(f, ndi.grey_erosion(f, footprint=EIGHT) + step)
        if np.array_equal(nf, f):
            break
        f = nf
    out = np.floor(f + 1e-9).astype(np.int8)
    out = np.maximum(out, LAND_TIER)
    out[sea] = SEA_TIER
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
    #
    # OJO con lo que el issue #61 pedia: el requisito real nunca fue que La
    # Grieta estuviera ALTA, era que no se viera INUNDADA. Subirla era la unica
    # herramienta que habia. Hoy La Grieta se pinta con el marron y baja al
    # fondo sin mojarse, asi que esto queda solo por la trama punteada --que
    # sigue siendo textura y sigue habiendo que promediarla-- y no por ella.
    g = np.where(land, ndi.gaussian_filter(g, 5.0), g)

    # Cortes sacados del histograma real del heightmap viejo: el mar en 0, la
    # meseta de tierra en 41, las sierras en 56/71 y las cumbres hasta 245.
    # Los cortes siguen siendo los seis del histograma viejo --el heightmap del
    # que sale el borrador tiene siete niveles, no diez-- y el resultado se
    # remapea a la escalera nueva con LEGACY_MAP. La fosa, la vega y la alta
    # montana las propone despues slope_limit, que es su trabajo.
    cuts = [8, 32, 50, 85, 130, 190]
    target = np.asarray(LEGACY_MAP, np.int8)[np.digitize(g, cuts)]
    target = np.where(land, np.maximum(target, LAND_TIER), SEA_TIER).astype(np.int8)

    grown = grow_apron(target, land, band_px)
    tier = slope_limit(grown, ~land, band_px)

    # La plataforma es una banda COSTERA por definicion: esta al nivel del mar,
    # y tierra adentro eso se ve como una laguna. El heightmap viejo dejaba los
    # valles de El Borde ahi abajo --issue #61-- asi que lo que no toca la
    # costa sube un escalon. Subir nunca crea un salto de nivel: los vecinos ya
    # eran >= 1.
    #
    # Esta regla se queda, pero por El Borde, no por La Grieta: La Grieta ya no
    # se arregla subiendola sino pintandola de marron y dejando que
    # carve_grieta() la hunda sin inundarla.
    d_sea = ndi.distance_transform_edt(land)
    tier[(tier == LAND_TIER) & (d_sea > band_px)] = LAND_TIER + 1
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
# --upgrade: migrar una mascara de la paleta vieja
# ---------------------------------------------------------------------------

def steal_guard(side, cand):
    """Saca de cand lo que borraria un componente entero de side.

    Las cumbres del mapa son manchas de un par de cientos de pixeles: una banda
    de 6 px abierta desde los dos lados se come algunas enteras, y perder la
    cumbre mas alta del continente en una migracion automatica no es aceptable.
    El componente que no sobrevive, no se toca.
    """
    lab, n = ndi.label(side, structure=EIGHT)
    if n == 0:
        return cand
    left = np.atleast_1d(ndi.sum(side & ~cand, lab, np.arange(1, n + 1)))
    doomed = np.zeros(n + 1, bool)
    doomed[1:] = left < 1
    return cand & ~doomed[lab]


def insert_band(tier, k, width):
    """Abre el escalon k --que no esta pintado-- a lo largo del borde entre sus
    dos vecinos, robandole mitad y mitad a cada uno.

    Es la forma de insertar un peldano SIN tocar el dibujo. La alternativa
    --reconstruir la escalera entera con grow_apron + slope_limit, que es lo
    que hace --trace-- aplasta el mapa: con tres escalones mas, subir del mar a
    la cumbre pasa a necesitar 7 bandas en vez de 5, y el relieve pintado no
    tiene esos pixeles de ancho. Medido sobre la mascara real: las cumbres y la
    alta montana desaparecian enteras, y las montanas quedaban en 1658 px de
    los 5535 dibujados.

    Insertando bandas angostas no se pierde nada: el mar, la playa, las colinas
    y las montanas quedan EXACTAMENTE donde estaban, y lo unico que cambia es
    que la subida que antes se repartia entre dos escalones ahora se reparte
    entre tres. Como los pasos de H tambien se achicaron, la ladera queda igual
    de tendida que antes.

    Devuelve (tier, pixeles asignados).
    """
    half = width / 2.0
    d_above = ndi.distance_transform_edt(~(tier >= k + 1))
    d_below = ndi.distance_transform_edt(~(tier <= k - 1))
    lo = steal_guard(tier == k - 1, (tier == k - 1) & (d_above <= half))
    hi = steal_guard(tier == k + 1, (tier == k + 1) & (d_below <= half))
    band = lo | hi
    out = tier.copy()
    out[band] = k
    return out, int(band.sum())


def upgrade(band_px=UPGRADE_BAND_PX, src_png=None):
    """Lleva una mascara de siete colores a la escalera de diez.

    Hace falta porque los dos escalones de tierra nuevos --la vega y la alta
    montana-- se meten EN EL MEDIO de la escalera vieja: una vez remapeados los
    indices, el verde (3) queda tocando al amarillo (5) y el rojo (7) al blanco
    (9). Eso es la regla de no-saltar rota en cada loma y en cada cordillera del
    mapa, y el script se niega a generar hasta que esten pintadas las dos bandas
    nuevas. A mano, alrededor de todo, es un dia de trabajo.

    No hay nada nuevo abajo de esto: "insertar las bandas intermedias que
    faltan" es literalmente lo que hace slope_limit --el piso de una funcion
    (1/band)-Lipschitz no puede tener un salto de nivel-- y grow_apron le pone
    antes a cada cosa alta el faldon que necesita para no quedar aplastada. Son
    las mismas dos funciones que usa --trace.

    Lo que el script NO puede proponer es la fosa ni la grieta: no estan en
    el dibujo viejo porque no existian. Eso se pinta a mano sobre el borrador.
    """
    src_png = src_png or TIERS_PNG
    if not os.path.exists(src_png):
        die('no esta %s, que es la mascara a migrar.' % short(src_png))

    tier = np.asarray(LEGACY_MAP, np.int8)[snap(src_png, LEGACY_PALETTE)]
    print('migrando %s  %dx%d  (paleta vieja de %d colores -> escalera de %d)'
          % (short(src_png), tier.shape[1], tier.shape[0],
             len(LEGACY_PALETTE), len(PALETTE)))

    missing = sorted(set(range(min(LEGACY_MAP), max(LEGACY_MAP) + 1))
                     - set(LEGACY_MAP))
    for k in missing:
        tier, took = insert_band(tier, k, band_px)
        print('  escalon %d (%s): banda de %d px abierta, %d px'
              % (k, NAMES[k], band_px, took))

    tier, specks = despeckle(tier)
    for t, n, px in specks:
        print('  despeckle: %d componentes sueltos del escalon %d (%s), %d px'
              % (n, t, NAMES[t], px))

    Image.fromarray(tier_to_rgb(tier)).save(DRAFT_PNG)
    print('  escrito %s' % os.path.relpath(DRAFT_PNG, ROOT))
    hist = np.bincount(tier.ravel(), minlength=len(PALETTE))
    for t, c in enumerate(hist):
        if c:
            print('    %d %-13s %7d px  %5.2f%%'
                  % (t, NAMES[t], c, 100 * c / tier.size))
    bad = validate(tier)
    print('  validacion del borrador: %s'
          % ('OK' if not bad else '\n    ' + '\n    '.join(bad)))
    comp = debug_composite(tier, os.path.join(HERE, 'map-tiers-draft-overlay.png'))
    if comp:
        print('  superposicion sobre la acuarela: %s' % os.path.relpath(comp, ROOT))

    print('\nAhora, sobre tools/map-tiers-draft.png:\n'
          '  - revisar las dos bandas que propuso el script: vega #80FF00 entre\n'
          '    tierra baja y llanura, alta montana #FF00FF entre montanas y\n'
          '    cumbres. Son automaticas, no estan dibujadas.\n'
          '  - pintar la FOSA ABISAL #00FFFF en el oceano profundo. Sin ella el\n'
          '    fondo del mar se queda en %.2f y no baja a 0.00.\n'
          '  - pintar la GRIETA SECA #804000 donde vaya, rodeada de tierra,\n'
          '    nunca tocando el agua.\n'
          'Guardarlo como tools/map-tiers.png y correr\n'
          '  python tools/make_heightmap.py --report --write-config\n'
          % H[SEA_TIER])


# ---------------------------------------------------------------------------
# El nivel del mar, del otro lado
# ---------------------------------------------------------------------------

# SEA_LEVEL sale de H[LAND_TIER] y queda horneado en el PNG, pero la ALTURA DEL
# PLANO DE AGUA la saca el sitio de map_3d_sea en _config.yml. Era el salto del
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
        print('\n%s:  %s: %s  coincide con H[LAND_TIER].' % (rel, CONFIG_KEY, m.group(2)))
        return True

    if write:
        src = src[:m.start()] + m.group(1) + want + src[m.end():]
        with open(path, 'w', encoding='utf-8', newline='') as fh:
            fh.write(src)
        print('\n%s:  %s  %s -> %s  (reescrito)'
              % (rel, CONFIG_KEY, m.group(2), want))
        return True

    print('\nEL NIVEL DEL MAR NO COINCIDE.\n'
          '  este heightmap:   H[LAND_TIER] = %s\n'
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
    ap.add_argument('--upgrade', action='store_true',
                    help='migra una mascara de la paleta vieja de 7 colores')
    ap.add_argument('--upgrade-src', metavar='PNG', default=None,
                    help='mascara a migrar (por defecto, tools/map-tiers.png)')
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
    ap.add_argument('--water', default=WATER_PNG,
                    help='mascara de agua para el visor (1 = agua)')
    ap.add_argument('--write-config', action='store_true',
                    help='corrige map_3d_sea en _config.yml en vez de solo avisar')
    args = ap.parse_args()

    if args.upgrade:
        upgrade(src_png=args.upgrade_src)
        return

    if args.trace:
        trace(src_png=args.trace_src)
        return

    if not os.path.exists(TIERS_PNG):
        die('no esta %s.\n'
            '  Para arrancar:  python tools/make_heightmap.py --trace'
            % os.path.relpath(TIERS_PNG, ROOT))

    tier, grieta = read_tiers(TIERS_PNG)
    print('mascara %s  %dx%d' % (os.path.relpath(TIERS_PNG, ROOT),
                                 tier.shape[1], tier.shape[0]))
    if grieta.any():
        print('  %s: %d px' % (GRIETA_NAME, int(grieta.sum())))

    tier, specks = despeckle(tier)
    for t, n, px in specks:
        print('  despeckle: %d componentes sueltos del escalon %d (%s), %d px'
              % (n, t, NAMES[t], px))
        if px > tier.size * 0.001:
            print('    ^ son muchos. Sintoma clasico de guardar la mascara como '
                  'JPEG o con antialiasing.')

    problems = validate(tier, os.path.join(HERE, 'map-tiers-problemas.png'),
                        grieta=grieta)
    if problems:
        head = 'la mascara tiene problemas:\n  - ' + '\n  - '.join(problems)

        # Una mascara de la paleta vieja valida perfecto contra la escalera
        # vieja y revienta contra esta, porque los dos escalones nuevos de
        # tierra se meten en el medio. Es un caso con nombre y con arreglo
        # automatico, asi que conviene decirlo en vez de dejar al que lee
        # pensando que se le rompio el dibujo.
        looks_legacy = not any((tier == k).any() for k in
                               set(range(min(LEGACY_MAP), max(LEGACY_MAP) + 1))
                               - set(LEGACY_MAP))
        if looks_legacy:
            head += ('\n\n  No hay ningun pixel de los escalones nuevos: esta '
                     'mascara parece estar\n  pintada con la paleta vieja de '
                     '%d colores. Para migrarla sola:\n'
                     '      python tools/make_heightmap.py --upgrade'
                     % len(LEGACY_PALETTE))
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

    h, _ = build_height(tier, grieta, verbose=args.report)
    field, repaired = finish(h, tier, grieta, blur_px=args.blur)

    small = (field.shape[1], field.shape[0])
    tier_small = np.asarray(
        Image.fromarray(tier.astype(np.uint8)).resize(
            small, Image.Resampling.NEAREST), np.int8)
    grieta_small = np.asarray(
        Image.fromarray(grieta.astype(np.uint8) * 255).resize(
            small, Image.Resampling.NEAREST), np.uint8) > 127
    zone_small = np.asarray(
        Image.fromarray(grieta_zone(grieta).astype(np.uint8) * 255).resize(
            small, Image.Resampling.NEAREST), np.uint8) > 127

    src_hash = hashlib.sha256(open(TIERS_PNG, 'rb').read()).hexdigest()[:16]
    arr = write_gray_png(args.out, field, {
        'Software': 'tools/make_heightmap.py',
        'Source': 'tools/map-tiers.png sha256:' + src_hash,
        'Palette': ';'.join('%02X%02X%02X' % c for c in PALETTE),
        'Heights': ';'.join('%.3f' % v for v in H),
        'SeaLevel': '%.3f' % SEA_LEVEL,
        'BowlSpanPx': str(BOWL_SPAN_PX),
        'BlurPx': '%.2f' % args.blur,
        'GrietaPx': str(int(grieta.sum())),
        'GrietaFloor': '%.3f' % GRIETA_FLOOR,
    })
    print('escrito %s  %dx%d, gris de 8 bits sin alfa, %d bytes'
          % (os.path.relpath(args.out, ROOT), arr.shape[1], arr.shape[0],
             os.path.getsize(args.out)))
    if repaired:
        print('  reparacion de orilla: %d px a resolucion plena (%.3f%%)'
              % (repaired, 100.0 * repaired / h.size))

    # La mascara de agua se escribe SIEMPRE, toda blanca si no hay grieta,
    # para que el visor tenga un solo camino: si el archivo pudiera faltar
    # habria que decidir en el JS que hacer cuando no esta, y esa rama seria
    # justo la que nadie prueba.
    warr = write_gray_png(args.water, build_water_mask(grieta), {
        'Software': 'tools/make_heightmap.py',
        'Source': 'tools/map-tiers.png sha256:' + src_hash,
        'Means': '255 = hay agua, 0 = grieta seca',
        'GrietaRimPx': str(GRIETA_RIM_PX),
    })
    print('escrito %s  %dx%d, %d bytes  (%s)'
          % (os.path.relpath(args.water, ROOT), warr.shape[1], warr.shape[0],
             os.path.getsize(args.water),
             'con agujero sobre la grieta' if grieta.any() else 'toda agua'))

    if args.report:
        below = report(field, tier_small, grieta_small, zone_small,
                       relief=args.relief)
        comp = debug_composite(tier, os.path.join(HERE, 'map-tiers-overlay.png'),
                               grieta=grieta)
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
