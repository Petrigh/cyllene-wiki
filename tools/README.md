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

Son siete colores, lo mas separados posible entre si a proposito. Cada pixel se
snapea al mas cercano, asi que un borde suavizado o un balde un poco corrido se
arreglan solos.

| color | escalon | que es |
|---|---|---|
| `#000000` negro | 0 | abismo / mar |
| `#0000FF` azul | 1 | plataforma, playa. **Esta justo al nivel del agua** |
| `#00FF00` verde | 2 | tierra baja |
| `#FFFF00` amarillo | 3 | llanura |
| `#FF8000` naranja | 4 | colinas |
| `#FF0000` rojo | 5 | montanas |
| `#FFFFFF` blanco | 6 | cumbres |

Las alturas de cada escalon estan en la tabla `H` de `make_heightmap.py`. Es
ahi donde se toca si el relieve no convence, y es casi lo unico que hay que
tocar.

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

- **El borde de la imagen tiene que ser todo mar.** El plano de agua es mas
  grande que el mapa y corta el canto de la malla, que no tiene faldon.
- **No se puede saltar un escalon.** Rojo no puede tocar amarillo: tiene que
  haber naranja en el medio. Es exactamente la regla que evita los acantilados,
  y el script se niega a generar si se rompe (y marca en magenta donde).

## Los comandos

```sh
pip install -r tools/requirements.txt

python tools/make_heightmap.py --trace     # borrador desde el heightmap viejo
python tools/make_heightmap.py --check     # valida la mascara y el nivel del mar
python tools/make_heightmap.py             # genera el heightmap
python tools/make_heightmap.py --report    # genera + diagnostico + imagenes

python tools/make_heightmap.py --write-config   # corrige map_3d_sea en _config.yml
python tools/make_heightmap.py --trace --trace-src otro.png
```

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
  salto maximo entre pixeles vecinos   5 niveles  (antes: 164)
  pendiente maxima en la malla         52.5 grados  (p99.9: 45.9)
  pixeles de tierra bajo el agua       0   <-- tiene que ser 0  (antes: 569)
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

## Si hay que tocar el nivel del mar

Vive en un solo lugar de verdad: `H[1]` en `make_heightmap.py`. De ahi sale el
gris del heightmap **y** tiene que salir `map_3d_sea` en `_config.yml`, que es
de donde el sitio saca la altura del plano de agua.

Son dos archivos, asi que **el script lo verifica**: al terminar compara `H[1]`
contra `map_3d_sea` y falla con codigo 1 si no coinciden. Para que lo corrija
solo:

```sh
python tools/make_heightmap.py --write-config
```

Por que esto esta atornillado asi: el nivel del mar viaja por tres saltos
(`H[1]` -> `map_3d_sea` -> `data-sea` -> el plano de agua del JS) y cuando se
rompe **no falla nada**, solo se hunde el mapa. Paso dos veces. La primera, el
JS tenia un `0.035` clavado que no sabia nada del dibujo. La segunda, el
navegador se quedo con un heightmap viejo en cache --meseta de tierra en 0.161--
y lo leyo con el `map_3d_sea` nuevo --agua en 0.247--: el continente entero bajo
el agua. Por eso ademas la URL del heightmap va versionada en
`_includes/campaign_map.html`, y el JS avisa por consola si menos del 15% de la
malla asoma del agua.

## Para subir o bajar el relieve en general

`map_3d_relief` en `_config.yml`. Es la exageracion vertical global y no cambia
las proporciones entre escalones: para eso esta la tabla `H`.
