# Como se dibuja el relieve del mapa

El heightmap del mapa 3D (`assets/img/map-height.png`) **no se pinta a mano**.
Se pinta `tools/map-tiers.png`, que es otra cosa: una mascara de **relleno
plano**, un color por escalon de terreno. El heightmap lo genera despues
`make_heightmap.py`.

## Por que

Se intento pintar el heightmap a mano y salio mal de cuatro maneras, todas la
misma: **el gris es la variable equivocada**. El gris fija la ALTURA, y lo que
hace que un terreno se lea no es la altura sino la PENDIENTE --altura sobre
distancia-- que ningun pincel controla.

| lo que se veia | por que |
|---|---|
| Las montanas demasiado altas y sin fundirse con el resto | gris 245 apoyado sobre gris 41: 200 niveles en un pixel. A la resolucion de la malla eso es una pared, y asi se sombrea, porque lo es |
| La costa poco natural | el mismo escalon, 0 -> 41, y trazada a 640x460 contra una acuarela de 1252x900 |
| El degrade del noreste no seguia el dibujo | no podia. La herramienta de degrade interpola en el espacio de la PANTALLA, en linea recta; una costa es una forma cualquiera |
| Tierra abajo del agua | ese degrade bajaba a negro y cruzaba el nivel del agua. 569 pixeles |

Con relleno plano el balde dibuja con precision y se corrige en dos clicks. Las
pendientes las fabrica el script con una transformada de distancia, y salen
continuas y acotadas **por construccion**: no hay forma de dibujar un
acantilado aunque uno quiera.

## La unica regla que hay que recordar

> **La pendiente la da el ANCHO de la banda que pintas, no su color.**

Para que una montana se funda con la llanura **no se baja su color**: se pinta
una banda de colinas **mas ancha** alrededor. El script reparte la subida a lo
largo del ancho que le des. Una montana angosta no queda parada: queda **mas
baja**, que es lo que le pasa a una montana angosta de verdad.

## La paleta

Son diez colores, lo mas separados posible entre si a proposito. Cada pixel se
snapea al mas cercano, asi que un borde suavizado o un balde un poco corrido se
arreglan solos.

| color | escalon | que es |
|---|---|---|
| `#00FFFF` cian | 0 | **fosa abisal**. El fondo del oceano |
| `#000000` negro | 1 | mar, plataforma continental |
| `#0000FF` azul | 2 | playa. **Su piso ES el nivel del agua** |
| `#00FF00` verde | 3 | tierra baja |
| `#80FF00` lima | 4 | vega, lomas bajas |
| `#FFFF00` amarillo | 5 | llanura |
| `#FF8000` naranja | 6 | colinas |
| `#FF0000` rojo | 7 | montanas |
| `#FF00FF` magenta | 8 | alta montana |
| `#FFFFFF` blanco | 9 | cumbres |

Y uno mas, que **no es un escalon** y se explica abajo:

| color | que es |
|---|---|
| `#804000` marron | grieta seca |

Las alturas de cada escalon estan en la tabla `H` de `make_heightmap.py`. Es
ahi donde se toca si el relieve no convence, y es casi lo unico que hay que
tocar.

El rango 0..1 del gris se reparte asi: **agua 0.00 a 0.40, tierra 0.40 a
1.00**. Antes la tierra terminaba en 0.82 y sobraba un 18% sin usar; ahora se
usa entero, y eso es lo que paga la profundidad del oceano sin achatar el
continente.

## El fondo del mar ahora se pinta

El negro ya no baja hasta el fondo. El mar (escalon 1) se hunde de la costa
hacia afuera hasta `H[1] = 0.22` y se queda ahi: eso es **plataforma
continental**. Para llegar al fondo de verdad --0.00-- hay que pintar la
**fosa** en cian, rodeada de negro.

Es a proposito: el relieve submarino pasa a ser algo que se dibuja, igual que
el de arriba. El precio es que un mapa sin cian tiene el oceano mas chato que
antes.

## La grieta seca

Una region tierra adentro que esta **muy por debajo del nivel del mar y que no
se inunda**. Se pinta en marron `#804000`, rodeada de tierra, y el script le
abre un tajo de paredes verticales que **baja hasta 0.00**, el piso absoluto
del rango: 0.40 por debajo del agua, tan hondo como la fosa abisal del oceano.

Existe por [La Grieta](../locations/regions/la_grieta.md), la falla que segun
[el orden de los planos](../lore/planos_taphaestri.md) da a los nueve infiernos
y al abismo. El mecanismo es general, pero el perfil esta elegido para eso.

> Ojo con el nombre: la **Hondonada de los faros** es otra region, en otro
> lugar del mapa, y no tiene nada que ver con esto. Por eso el color marron se
> llama *grieta* y no *hondonada*.

**No es un escalon de la escalera, y no puede serlo.** Vale la pena entender
por que, porque explica las dos reglas raras que tiene:

La escalera es monotona en altura y la regla de no-saltar obliga a recorrerla
de forma continua *en el espacio*. Una grieta rodeada de tierra alta tendria
que bajar pasando por todos los escalones intermedios; si su piso esta bajo el
nivel del mar, esos escalones intermedios tambien lo estan, y todo escalon por
debajo de la playa **es mar**. O sea: para pintarla como escalon habria que
pintar mar tierra adentro, que es un lago, no una grieta. Y al reves: un
escalon seco por debajo del mar tendria que ir entre el mar y la playa en la
escalera, y entonces la regla de no-saltar obligaria a pintarlo como una banda
a lo largo de **toda la costa**.

Asi que es un recorte aparte. Dos consecuencias practicas:

- **No se le aplica la regla de no-saltar.** El marron puede tocar cualquier
  escalon de tierra, porque antes de validar el script lo reemplaza por el
  escalon que lo rodea. El empalme del borde sale continuo solo.
- **No puede tocar el agua.** Pegada al mar no es una grieta, es un tajo seco
  al lado del oceano. El script lo rechaza.

### El perfil: pared y piso, no cuenca

La caida ocupa los primeros `GRIETA_WALL_PX` (4 px) y de ahi para adentro el
piso es plano. **La profundidad no depende del ancho**: una grieta de 20 px y
una de 200 llegan las dos al fondo.

Es a proposito, y costo una iteracion. La primera version repartia la bajada a
lo largo de un span de 60 px desde el borde, como hace el domo con los picos.
Para una cuenca esta bien; para una falla es inservible, porque ata la
profundidad al ancho: una grieta de 20 px quedaba en 0.421, **por encima del
nivel del mar**, y habia que pintarla de 120 px --el 10% del continente-- para
que tocara el piso.

La pared da ~80 grados. El reporte la mide aparte justamente porque es una
pared a proposito: si entrara en el estadistico general lo taparia.

### El ancho minimo, que es lo unico que hay que saber antes de pintar

La profundidad ya no depende del ancho, pero la **resolucion** si: el
desenfoque de `BLUR_PX` rellena el piso de un tajo angosto. Medido:

| ancho pintado | piso que queda | profundidad que sobrevive |
|---|---|---|
| 10 px | 0.181 | 59% |
| 14 px | 0.083 | 81% |
| 16 px | 0.053 | 88% |
| **20 px** | 0.018 | **96%** |
| **30 px** | 0.000 | **100%** |

**Pintarla de 20 px o mas**, 30 si se quiere el fondo exacto. Abajo de 16 el
script avisa, con el ancho medido del componente mas angosto.

Y un componente de menos de `GRIETA_MIN_PX` (64 px) se descarta como borron del
pincel: con este perfil cualquier mancha de mas de 8 px de ancho cae entera al
fondo, asi que un descuido del balde abre un agujero al infierno.

Del lado del visor hay una pieza mas: el agua del mapa 3D es **un solo plano
translucido** que cubre todo, asi que sin ayuda taparia la grieta como si
fuera un lago. Por eso el generador escribe tambien `assets/img/map-water.png`,
una mascara que le agujerea el agua justo encima. Se publica junto al
heightmap y no hay que tocarla nunca.

## Como se pinta

Sirve cualquier editor con balde: GIMP, Krita, Paint.NET, o
[Photopea](https://photopea.com) directo en el navegador sin instalar nada.

1. Abrir `tools/map-tiers.png`.
2. Poner `assets/img/map.jpg` en una capa **abajo**, y bajarle la opacidad a la
   mascara para ir calcando.
3. Balde y lapiz, nada mas. **El suavizado (anti-aliasing) APAGADO.**
4. Guardar como **PNG**. Nunca JPEG: un JPEG hace halos en cada borde y
   desparrama pixeles de escalon equivocado, y para una transformada de
   distancia un pixel suelto es catastrofico --un pixel de montana en el oceano
   no solo hace un pincho, deforma el terreno a cientos de pixeles a la redonda.

Dos reglas que el script verifica y que conviene tener presentes mientras se
dibuja:

- **El borde de la imagen tiene que ser todo agua** --negro o cian--. El plano
  de agua es mas grande que el mapa y corta el canto de la malla, que no tiene
  faldon.
- **No se puede saltar un escalon.** Rojo no puede tocar amarillo: tienen que
  estar naranja y lima en el medio. Es exactamente la regla que evita los
  acantilados, y el script se niega a generar si se rompe (y marca en **gris**
  donde).
- El marron de la grieta queda **afuera** de las dos reglas de arriba: puede
  tocar cualquier escalon de tierra, y no puede tocar el agua ni el borde.

## Los comandos

```sh
pip install -r tools/requirements.txt

python tools/make_heightmap.py --upgrade   # migra una mascara de 7 colores
python tools/make_heightmap.py --trace     # borrador desde el heightmap viejo
python tools/make_heightmap.py --check     # valida la mascara y el nivel del mar
python tools/make_heightmap.py             # genera el heightmap
python tools/make_heightmap.py --report    # genera + diagnostico + imagenes

python tools/make_heightmap.py --write-config   # corrige map_3d_sea en _config.yml
python tools/make_heightmap.py --trace --trace-src otro.png
```

## Migrar una mascara vieja: `--upgrade`

Una mascara pintada con la paleta de siete colores **no valida** contra la
escalera de diez, porque los dos escalones de tierra nuevos --la vega y la alta
montana-- se meten en el medio: el verde queda tocando al amarillo y el rojo al
blanco, que es la regla de no-saltar rota en cada loma del mapa. El script lo
detecta y lo dice.

```sh
python tools/make_heightmap.py --upgrade
```

Abre las dos bandas que faltan a lo largo del borde entre sus vecinos,
robandoles 3 px a cada lado, y deja `map-tiers-draft.png` **validando**. El
dibujo no se toca: el mar, la playa, las colinas y las montanas quedan
exactamente donde estaban, y lo unico que cambia es que la subida que antes se
repartia entre dos escalones ahora se reparte entre tres. Como los pasos de `H`
tambien se achicaron, la ladera queda igual de tendida.

Lo que `--upgrade` **no** puede proponer es la fosa ni la grieta: no estan
en el dibujo viejo porque no existian. Eso se pinta a mano sobre el borrador.

> No usar `--trace` para esto. `--trace` reconstruye la escalera entera desde
> cero, y con tres escalones mas subir del mar a la cumbre pasa a necesitar 7
> bandas en vez de 5: medido sobre la mascara real, las cumbres y la alta
> montana desaparecian enteras y las montanas quedaban en 1.658 px de los 5.535
> dibujados.

`--trace` sale, por defecto, del `map-height.png` publicado. Una vez que se
genero el heightmap nuevo ese archivo **ya no es el pintado a mano**, asi que
para volver al original:

```sh
git show HEAD:assets/img/map-height.png > tools/old-height.png
python tools/make_heightmap.py --trace --trace-src tools/old-height.png
```

`--trace` arma `map-tiers-draft.png` portando el heightmap pintado a mano al
formato nuevo: conserva la intencion de altura que ya estaba dibujada, le pone
a cada montana el faldon que le faltaba y deja todo validando. Se renombra a
`map-tiers.png` y a partir de ahi se corrige a mano. Tambien deja
`map-tiers-draft-overlay.png`, los bordes de los escalones sobre la acuarela,
que es donde se ve si la costa esta corrida respecto de la linea de tinta.

**La costa es justamente lo que el borrador no puede saber**, y es la pasada a
mano que hay que hacer si o si. El borrador decide tierra-o-mar con un umbral de
gris sobre el heightmap viejo (`TRACE_SEA_CUT = 8`), asi que todo lo que el
dibujo pinto por debajo de ese gris se vuelve oceano. Medido contra el heightmap
pintado a mano: **5.652 px en 268 componentes**, el mas grande en el noreste
(x 68-87%, y 11-33%), que es donde estaba el degrade que bajaba a negro.

Es el bug original cambiado de forma: antes era tierra pintada **abajo** del
agua, ahora es tierra del dibujo que la mascara declara **mar**. Se ve igual en
la malla, y ni el assert ni `--report` lo ven, porque para ellos esos pixeles ya
no son tierra. Por eso `--trace` los lista con su posicion: es el unico momento
del camino donde esa informacion todavia existe.

## Como se lee `--report`

```
  salto maximo entre pixeles vecinos   6 niveles  (antes: 164)
  pendiente maxima en la malla         52.4 grados  (p99.9: 42.9)   [sin la grieta]
  pixeles de tierra bajo el agua       0   <-- tiene que ser 0  (antes: 569)
  grieta seca                          1555 px, piso 0.000 (0.400 bajo el mar)
    pared ~80 grados en 4 px   <-- es una pared a proposito
```

- **Pixeles de tierra bajo el agua: tiene que ser 0.** Es el test del bug
  original. No deberia poder dar otra cosa, porque el nivel del mar es el piso
  del escalon 1 y la tierra queda arriba por construccion; si da distinto de 0
  hay un bug en el script, no en el dibujo.
- **Pendiente maxima**: arriba de ~55 grados el ojo empieza a leer "pared" en
  vez de "monte". Si se pasa, **ensanchar la banda que este parada**, no bajarle
  el color.
- **Salto maximo**: cuanto cambia el gris entre dos pixeles vecinos. El
  heightmap pintado a mano llegaba a 164.
- **Grieta seca**: cuanto bajo. Es la unica tierra que queda debajo del agua,
  por eso se informa aparte y no cuenta en la linea de arriba. Tiene que dar
  piso `0.000`; si da mas alto, esta pintada demasiado angosta.
- **El salto y la pendiente se miden sin la grieta** --lo dice la linea--. Su
  pared da ~80 grados y ~26 niveles siempre y a proposito, y si entraran
  taparian las dos metricas que sirven para ver si el *resto* del mapa esta
  bien.

## Si hay que tocar el nivel del mar

Vive en un solo lugar de verdad: `H[LAND_TIER]` en `make_heightmap.py` --hoy,
`0.40`--. De ahi sale el gris del heightmap **y** tiene que salir `map_3d_sea`
en `_config.yml`, que es de donde el sitio saca la altura del plano de agua.

Son dos archivos, asi que **el script lo verifica**: al terminar compara
`H[LAND_TIER]` contra `map_3d_sea` y falla con codigo 1 si no coinciden. Para que lo corrija
solo:

```sh
python tools/make_heightmap.py --write-config
```

Por que esto esta atornillado asi: el nivel del mar viaja por tres saltos
(`H[LAND_TIER]` -> `map_3d_sea` -> `data-sea` -> el plano de agua del JS) y
cuando se rompe **no falla nada**, solo se hunde el mapa. Paso dos veces. La primera, el
JS tenia un `0.035` clavado que no sabia nada del dibujo. La segunda, el
navegador se quedo con un heightmap viejo en cache --meseta de tierra en 0.161--
y lo leyo con el `map_3d_sea` nuevo --agua en 0.247--: el continente entero bajo
el agua. Por eso ademas la URL del heightmap va versionada en
`_includes/campaign_map.html`, y el JS avisa por consola si menos del 15% de la
malla asoma del agua.

## Para subir o bajar el relieve en general

`map_3d_relief` en `_config.yml`. Es la exageracion vertical global y no cambia
las proporciones entre escalones: para eso esta la tabla `H`.
