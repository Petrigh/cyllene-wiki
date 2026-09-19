---
title: Salud del wiki
permalink: /meta/
backlinks: false
# Los documentos de coleccion generan excerpt, y el primer bloque Liquid de esta
# pagina tiene renglones en blanco adentro: Jekyll avisa que "modifico" el
# excerpt para cerrarlo. No se usa para nada, asi que se apaga.
excerpt_separator: ""
# Un documento de coleccion sin `date:` toma site.time, o sea la hora del build,
# y jekyll-seo-tag la escribe en el <head>. Eso hace que dos builds seguidos den
# archivos distintos y arruina el chequeo que importa: construir dos veces y
# comparar es lo unico que detecta un error de orden de render en los chequeos
# que miran el cuerpo. Con la fecha fija, un diff que no da vacio es una falla
# de verdad.
date: 2026-09-18
---

{%- comment -%}
  Pagina de mantenimiento: junta en una sola lista todo lo que en el wiki falla
  EN SILENCIO. Es la contracara de backlinks.html -- aquel bloque mostro lo
  despareja que esta la cobertura, esta pagina la pone en numeros.

  El peor caso es `summary:`. Alimenta tres cosas a la vez (los tooltips del
  mapa, el arbol de locations/index.md y cada fila de los indices de seccion) y
  las tres degradan sin avisar: un "if kid.summary" sin else simplemente no
  dibuja nada. Lo mismo un link muerto o un `location:` mal escrito: la pagina
  sale igual, solo que sin el link.

  (En los comentarios de este archivo no se escriben llaves de Liquid ni en los
  ejemplos: Liquid parsea el cuerpo de un comment igual que el resto, asi que un
  "if" de ejemplo sin su "endif" rompe el build.)

  ---- Esta pagina NO se publica -----------------------------------------

  Es una vista de mantenimiento, no contenido. Que no llegue a GitHub Pages no
  es una convencion sino una garantia, y sale de tres hechos que se combinan:

  1. Jekyll::EntryFilter#special? descarta toda entrada cuyo nombre empiece con
     "_", y corre sobre Dir.entries ANTES de que Jekyll baje al directorio. Una
     carpeta _ sin declarar no se recorre: ni pagina, ni documento, ni static
     file, ni copia.
  2. Lo unico que saltea ese filtro es Jekyll::Collection#read, que hace glob
     sobre _<label> explicitamente. Sin `collections: meta:` no hay glob, y
     entonces _meta/ no existe para el build.
  3. GitHub Pages construye leyendo _config.yml y nada mas; .github/ tiene solo
     CODEOWNERS, no hay workflow que cambie eso.

  Por eso la coleccion se declara SOLO en _config_local.yml, que se pasa a mano
  con --config desde el `command:` de docker-compose.yml. Ver el comentario
  tripwire en _config.yml.

  Corolario practico: nunca enlazar /meta/ desde una pagina de contenido, porque
  en produccion seria un 404. El acceso es el aux_link "Salud del wiki", que
  tambien vive solo en la config local.

  Otro corolario, este a favor: como es un documento de coleccion y no una
  pagina, no esta en site.html_pages, asi que NO entra en el indice de busqueda
  y su contenido enorme no infla search-data.json. Y hereda `layout: wiki_base`
  del scope de todo el sitio, asi que backlinks.html corre aca tambien, pero no
  cuesta nada: /meta/ no tiene ".html" en la url y la guarda lo apaga de una.

  ---- jekyll-relative-links no toca esta pagina --------------------------

  El gem solo procesa site.pages, no los documentos de coleccion. Un link
  relativo .md escrito aca NO se reescribe y sale muerto. Todos los links de
  esta pagina se arman con `relative_url` sobre la url ya resuelta.

  ---- La regla del orden de render --------------------------------------

  site.pages[].content es markdown crudo para las paginas que todavia no se
  renderizaron y HTML convertido para las que si, y Jekyll no garantiza el
  orden. Cualquier chequeo que mire el cuerpo tiene que dar el MISMO resultado
  en las dos formas, o esta pagina cambiaria de build en build.

  El conjunto de paginas cuyo contenido no es invariante al orden ya esta
  identificado y marcado desde backlinks.html: son los diez index.md, que arman
  sus listas con Liquid. Se reconocen con el mismo predicado que usa aquel: url
  con ".html" y `backlinks` distinto de false. Eso es hs_scan, aca abajo. No
  inventar otra lista.

  factions/party.md estuvo en ese conjunto mientras su roster salia de un for.
  Desde que los links a los PC se escriben a mano y Liquid solo completa las
  celdas de datos, el cuerpo dejo de depender del orden y la pagina entro aca.

  Ojo con la otra punta: lore/calendario.md y rules/table-rulings.md llevan
  `backlinks: false` sin tener una linea de Liquid en el cuerpo. Lo usan para
  apagar el bloque de menciones, y como el predicado es compartido eso las saca
  tambien de hs_scan y del grafo. No es un problema de orden de render: es el
  precio de tener un solo flag para tres sistemas.

  Las variables llevan prefijo hs_ a proposito: en Jekyll los assign de un
  include escriben en el scope global (bl_ backlinks, wc_ ficha, lc_ arbol de
  ubicaciones).

  ---- Por que la cuenta va toda arriba y el texto todo abajo -------------

  Kramdown se come el primer renglon que sigue a un titulo cuando no hay linea
  en blanco de por medio: el h2 termina con el id
  "sin-summary97-paginas-no-tienen-summary-es-el-campo..." y el parrafo
  desaparece adentro del titulo. Con los recortes de espacio de Liquid ({%- y
  -%}) esa linea en blanco se evapora facilisimo, y no se ve hasta que se mira
  el HTML.

  Por eso el archivo esta partido en dos: PRIMERO todos los chequeos, que no
  imprimen nada y guardan su resultado ya armado en un hs_out_*, y DESPUES el
  documento, que es markdown comun con lineas en blanco de verdad y una sola
  salida hs_out_* por seccion. Mientras el texto de abajo no tenga logica, no
  hay recorte que pueda pegotear un titulo con lo que le sigue.

  ---- Presentacion -------------------------------------------------------

  Cero SCSS. _sass/custom/custom.scss compila dentro de la hoja de estilos
  PUBLICADA, asi que cualquier regla .health-* viajaria a produccion como bytes
  muertos y filtraria la existencia de esta pagina. No hace falta: details/
  summary ya es el idiom de la casa, y code/ul/h2 los tematiza just-the-docs.
  Para los datos secundarios se reusa .loc-todo, que ya se publica y significa
  exactamente "falta escribir esto".

  A nivel SECCION se invierte la regla de locations/index.md: en vez de
  desaparecer cuando no hay nada, dice "todo OK" -- en una pagina de control,
  cero hallazgos es la noticia. Los sub-bloques si desaparecen.
{%- endcomment -%}

{%- comment -%}
  Las paginas que se pueden mirar por dentro sin riesgo. Ver "la regla del orden
  de render" arriba.
{%- endcomment -%}
{%- assign hs_scan = site.pages | where_exp: "hs_p", "hs_p.url contains '.html'" | where_exp: "hs_p", "hs_p.backlinks != false" -%}

{%- comment -%}
  `parent:` es el discriminador de seccion confiable: las paginas de contenido lo
  tienen y los diez index.md no, asi que filtrar por parent los deja afuera solo,
  sin lista de excepciones.
{%- endcomment -%}
{%- assign hs_secs = "Characters,The Party,Locations,Sessions,Items,Quests,Factions,Lore,Bestiary,House Rules,Leyendas de Aira" | split: "," -%}


{%- comment -%}
  ======================================================================
  1. Sin summary
  ======================================================================

  Front matter puro: O(n) y totalmente invariante al orden. Una pasada por
  seccion, y cada seccion se dibuja solo si tiene algo (bestiary, rules y la
  party hoy no producen nada).

  Falta el summary tanto si no esta la clave como si esta y quedo vacia, que a
  la vista es lo mismo. Eso son dos condiciones, y aca no se puede usar
  where_exp: el parse_condition de Jekyll acepta UNA sola comparacion y corta
  con "Expected end_of_string" apenas ve un `or`. Asi que va un for a mano, que
  igual son las ~195 paginas una sola vez, con el mismo filtro `default | strip`
  que usa la ficha para decidir si un campo se dibuja.

  El acumulador se arma capturando sobre si mismo y dejando el salto de linea
  antes del <details> adentro de la captura: asi los bloques quedan separados
  por una linea en blanco, que es lo que kramdown necesita para reconocer cada
  uno como HTML de bloque.
{%- endcomment -%}
{%- assign hs_sum_total = 0 -%}
{%- assign hs_sum_body = "" -%}
{%- for hs_sec in hs_secs -%}
  {%- assign hs_kids = site.pages | where: "parent", hs_sec | sort: "title" -%}
  {%- assign hs_rows = "" -%}
  {%- assign hs_n = 0 -%}
  {%- for hs_p in hs_kids -%}
    {%- assign hs_plain = hs_p.summary | default: "" | strip -%}
    {%- if hs_plain != "" -%}{%- continue -%}{%- endif -%}
    {%- assign hs_n = hs_n | plus: 1 -%}
    {%- capture hs_row -%}<li><a href="{{ hs_p.url | relative_url }}">{{ hs_p.title | default: hs_p.path }}</a> <code class="loc-todo">{{ hs_p.path }}</code></li>{%- endcapture -%}
    {%- assign hs_rows = hs_rows | append: hs_row -%}
  {%- endfor -%}
  {%- if hs_n > 0 -%}
    {%- assign hs_sum_total = hs_sum_total | plus: hs_n -%}
    {%- capture hs_sum_body -%}{{ hs_sum_body }}
<details>
<summary><b>{{ hs_sec }}</b> — {{ hs_n }} de {{ hs_kids.size }}</summary>
<ul>{{ hs_rows }}</ul>
</details>
{% endcapture -%}
  {%- endif -%}
{%- endfor -%}
{%- capture hs_out_sum -%}
{%- if hs_sum_total == 0 -%}
Todo OK.
{%- else -%}
**{{ hs_sum_total }} paginas** no tienen `summary:`. Es el campo que mas duele
que falte: lo leen los tooltips del mapa, el arbol de `locations/index.md` y
cada fila de los indices de seccion, y los tres se degradan sin decir nada.
{{ hs_sum_body }}
{%- endif -%}
{% endcapture %}


{%- comment -%}
  ======================================================================
  2. Sesiones
  ======================================================================

  `date:` y `summary:` son front matter, asi que son triviales. "Sin notas" mira
  el cuerpo, y ahi hay que tener cuidado.

  Contar CARACTERES no sirve, y no solo cerca del umbral: es inseguro siempre.
  Un link a Iri escrito en markdown mide 33 caracteres crudo y 57 renderizado,
  asi que una sesion con muchos links cruza cualquier umbral de bytes segun en
  que orden le toco renderizarse. Dos señales que no se mueven:

  1. Tiene links = aparece ".html" en el cuerpo. Despues de que
     jekyll-relative-links corre (en :generate, antes de que se renderice nada)
     un link es "](/cyllene-wiki/.../iri.html)" o
     "href=/cyllene-wiki/.../iri.html" -- un ".html" por link en las dos formas,
     y ".html" no aparece en ningun otro lado del cuerpo de una sesion.
     Exactamente invariante.

  2. Palabras despues de strip_html y normalize_whitespace. Ningun path de este
     wiki tiene espacios, asi que un link inline en markdown da la misma cuenta
     de tokens que su forma renderizada. La deriva medida sobre las 32 sesiones
     es exactamente +1 en crudo (el "#" del H1). normalize_whitespace ademas se
     come el \r que dejan los CRLF de todo el corpus.

  El test es links == 0 Y palabras < 8. Los datos son bimodales con un hueco
  ancho: los 8 stubs son 4-5 palabras y 0 links, y la nota real mas corta
  (sesion 22) tiene 11-12 palabras y 2 links. El 8 queda a tres palabras de cada
  lado, tres veces la peor deriva medida, y ademas solo decide cuando el termino
  de deriva cero ya se disparo.
{%- endcomment -%}
{%- assign hs_sess = site.pages | where: "parent", "Sessions" | sort: "title" -%}
{%- assign hs_row_notes = "" -%}
{%- assign hs_row_sum = "" -%}
{%- assign hs_row_date = "" -%}
{%- assign hs_n_notes = 0 -%}
{%- assign hs_n_sum = 0 -%}
{%- assign hs_n_date = 0 -%}
{%- for hs_s in hs_sess -%}
  {%- capture hs_link -%}<a href="{{ hs_s.url | relative_url }}">{{ hs_s.title }}</a>{%- endcapture -%}

  {%- unless hs_s.date -%}
    {%- assign hs_n_date = hs_n_date | plus: 1 -%}
    {%- assign hs_row_date = hs_row_date | append: "<li>" | append: hs_link | append: "</li>" -%}
  {%- endunless -%}

  {%- assign hs_plain = hs_s.summary | default: "" | strip -%}
  {%- if hs_plain == "" -%}
    {%- assign hs_n_sum = hs_n_sum | plus: 1 -%}
    {%- assign hs_row_sum = hs_row_sum | append: "<li>" | append: hs_link | append: "</li>" -%}
  {%- endif -%}

  {%- assign hs_words = hs_s.content | strip_html | normalize_whitespace | number_of_words -%}
  {%- assign hs_stub = true -%}
  {%- if hs_s.content contains ".html" -%}{%- assign hs_stub = false -%}{%- endif -%}
  {%- if hs_words >= 8 -%}{%- assign hs_stub = false -%}{%- endif -%}
  {%- if hs_stub -%}
    {%- assign hs_n_notes = hs_n_notes | plus: 1 -%}
    {%- capture hs_tail -%} <code class="loc-todo">{{ hs_words }} palabras, sin links</code>{%- endcapture -%}
    {%- assign hs_row_notes = hs_row_notes | append: "<li>" | append: hs_link | append: hs_tail | append: "</li>" -%}
  {%- endif -%}
{%- endfor -%}
{%- capture hs_out_sess -%}
{%- if hs_n_notes == 0 and hs_n_sum == 0 and hs_n_date == 0 -%}
Todo OK, las {{ hs_sess.size }} sesiones estan completas.
{%- else -%}
Sobre {{ hs_sess.size }} sesiones.
{% if hs_n_notes > 0 %}
<details open>
<summary><b>Sin notas</b> — {{ hs_n_notes }}</summary>
<ul>{{ hs_row_notes }}</ul>
</details>
{% endif %}
{%- if hs_n_sum > 0 %}
<details>
<summary><b>Sin <code>summary:</code></b> — {{ hs_n_sum }}</summary>
<ul>{{ hs_row_sum }}</ul>
</details>
{% endif %}
{%- if hs_n_date > 0 %}
<details>
<summary><b>Sin <code>date:</code></b> — {{ hs_n_date }}</summary>
<ul>{{ hs_row_date }}</ul>
</details>
{% endif %}
{%- endif -%}
{% endcapture %}


{%- comment -%}
  ======================================================================
  3a. Links .md muertos
  ======================================================================

  jekyll-relative-links reescribe un link relativo .md SOLO cuando el destino
  existe. Asi que cualquier ".md" que siga en el cuerpo despues de :generate
  esta roto por definicion: no hay que resolver ningun path, alcanza con
  encontrarlo.

  Se buscan las dos formas porque el orden de render no esta garantizado: el
  parentesis del markdown crudo y el atributo href del HTML convertido. Las dos
  se recorren siempre; la que no corresponde no encuentra nada, porque el
  markdown ya no existe una vez convertido y el href todavia no existe antes.

  El `contains ".md"` de arriba es la guarda barata: hoy solo un puñado de
  paginas entra al split, las otras ~190 se descartan con un include? de Ruby.

  OJO: el gem tampoco reescribe destinos absolutos ni relativos a la raiz. Hoy
  no hay ninguno, asi que el chequeo es exacto, pero un futuro
  "[x](/locations/foo.md)" seria un falso positivo aca.
{%- endcomment -%}
{%- assign hs_dead = "" -%}
{%- assign hs_n_dead = 0 -%}
{%- for hs_p in hs_scan -%}
  {%- unless hs_p.content contains ".md" -%}{%- continue -%}{%- endunless -%}

  {%- assign hs_found = "" -%}
  {%- assign hs_chunks = hs_p.content | split: "](" -%}
  {%- for hs_c in hs_chunks offset: 1 -%}
    {%- assign hs_d = hs_c | split: ")" | first -%}
    {%- if hs_d contains ".md" -%}{%- assign hs_found = hs_found | append: hs_d | append: "," -%}{%- endif -%}
  {%- endfor -%}
  {%- assign hs_chunks = hs_p.content | split: 'href="' -%}
  {%- for hs_c in hs_chunks offset: 1 -%}
    {%- assign hs_d = hs_c | split: '"' | first -%}
    {%- if hs_d contains ".md" -%}{%- assign hs_found = hs_found | append: hs_d | append: "," -%}{%- endif -%}
  {%- endfor -%}

  {%- assign hs_dests = hs_found | split: "," -%}
  {%- for hs_d in hs_dests -%}
    {%- assign hs_n_dead = hs_n_dead | plus: 1 -%}
    {%- capture hs_row -%}<li><a href="{{ hs_p.url | relative_url }}">{{ hs_p.title }}</a> — <code>{{ hs_d }}</code></li>{%- endcapture -%}
    {%- assign hs_dead = hs_dead | append: hs_row -%}
  {%- endfor -%}
{%- endfor -%}
{%- capture hs_out_dead -%}
{%- if hs_n_dead == 0 -%}
Todo OK.
{%- else -%}
{{ hs_n_dead }} links apuntan a un `.md` que no existe. El destino se muestra
tal cual esta escrito en el cuerpo.

<ul>{{ hs_dead }}</ul>
{%- endif -%}
{% endcapture %}


{%- comment -%}
  ======================================================================
  3b. Front matter que no resuelve
  ======================================================================

  Los campos que la ficha convierte en link, con la seccion donde tiene que
  buscar el destino. Es el mismo mapa que wc_fields en wiki_card.html y que la
  tabla en prosa del encabezado de backlinks.html.

  ATENCION: el mapa vive hoy en esos TRES lugares y tienen que coincidir. Si se
  agrega o se cambia un campo hay que tocar los tres. (Lo correcto seria subirlo
  a _config.yml como `card_fields:` y que los tres lean site.card_fields, pero
  eso toca el camino caliente -- la ficha se dibuja en ~140 paginas -- y merece
  su propio cambio.)

  Los indices de titulos por seccion se arman UNA vez como strings separados por
  "|" y se prueba pertenencia con `contains` sobre una aguja envuelta en "|".
  Ningun titulo del wiki contiene un "|", asi que no hay ambiguedad.

  Se separan dos casos, y el segundo es el interesante:

  - no resuelve a nada -> wiki_link.html devuelve el texto pelado. Molesto, pero
    visible en la ficha.
  - resuelve pero en la seccion EQUIVOCADA -> wiki_link.html se cae a
    `wl_cands | first` y enlaza a la pagina incorrecta, en silencio. Hoy no pasa
    ninguna vez; es exactamente la trampa que el cuarto elemento de wc_fields
    vino a tapar (cinco titulos existen dos veces: Verna, Brolwund, Carnahan,
    Glavok y Naivara son NPC y asentamiento a la vez), asi que esto se queda
    como guarda de regresion.
{%- endcomment -%}
{%- assign hs_idx_all = site.pages | map: "title" | join: "|" | prepend: "|" | append: "|" -%}
{%- assign hs_idx_characters = site.pages | where_exp: "hs_p", "hs_p.url contains '/characters/'" | map: "title" | join: "|" | prepend: "|" | append: "|" -%}
{%- assign hs_idx_locations  = site.pages | where_exp: "hs_p", "hs_p.url contains '/locations/'"  | map: "title" | join: "|" | prepend: "|" | append: "|" -%}
{%- assign hs_idx_factions   = site.pages | where_exp: "hs_p", "hs_p.url contains '/factions/'"   | map: "title" | join: "|" | prepend: "|" | append: "|" -%}
{%- assign hs_idx_lore       = site.pages | where_exp: "hs_p", "hs_p.url contains '/lore/'"       | map: "title" | join: "|" | prepend: "|" | append: "|" -%}

{%- assign hs_fields = "holder|characters,leader|characters,seat|locations,world|locations,continent|locations,region|locations,settlement|locations,location|locations,faction|factions,pantheon|lore" | split: "," -%}
{%- assign hs_fm_none = "" -%}
{%- assign hs_fm_wrong = "" -%}
{%- assign hs_n_none = 0 -%}
{%- assign hs_n_wrong = 0 -%}
{%- for hs_f in hs_fields -%}
  {%- assign hs_pair = hs_f | split: "|" -%}
  {%- comment -%}
    La clave va a una variable suelta por lo mismo que wc_key en
    wiki_card.html: Liquid no resuelve un lookup con indice anidado adentro.
  {%- endcomment -%}
  {%- assign hs_key = hs_pair[0] -%}
  {%- assign hs_sec = hs_pair[1] -%}
  {%- if hs_sec == "characters" -%}{%- assign hs_idx = hs_idx_characters -%}
  {%- elsif hs_sec == "locations" -%}{%- assign hs_idx = hs_idx_locations -%}
  {%- elsif hs_sec == "factions" -%}{%- assign hs_idx = hs_idx_factions -%}
  {%- else -%}{%- assign hs_idx = hs_idx_lore -%}{%- endif -%}

  {%- comment -%}
    where_exp filtra del lado de Ruby: las ~195 paginas se recorren una vez por
    campo sin pagar el interprete de Liquid, y al for de abajo solo llegan las
    que realmente tienen la clave.
  {%- endcomment -%}
  {%- assign hs_users = site.pages | where_exp: "hs_p", "hs_p[hs_key]" -%}
  {%- for hs_p in hs_users -%}
    {%- assign hs_val = hs_p[hs_key] -%}
    {%- comment -%}
      Mismo filtro que la ficha: sacandole los guiones tiene que quedar algo,
      asi se saltean de una el vacio y el "-" que varios items usan de
      placeholder, que tampoco se dibuja como link.
    {%- endcomment -%}
    {%- assign hs_plain = hs_val | replace: "-", "" | strip -%}
    {%- if hs_plain == "" -%}{%- continue -%}{%- endif -%}

    {%- capture hs_needle -%}|{{ hs_val }}|{%- endcapture -%}
    {%- if hs_idx contains hs_needle -%}{%- continue -%}{%- endif -%}

    {%- capture hs_head -%}<li><a href="{{ hs_p.url | relative_url }}">{{ hs_p.title }}</a> — <code>{{ hs_key }}: {{ hs_val }}</code>{%- endcapture -%}
    {%- if hs_idx_all contains hs_needle -%}
      {%- assign hs_n_wrong = hs_n_wrong | plus: 1 -%}
      {%- assign hs_bad = site.pages | where: "title", hs_val | first -%}
      {%- capture hs_row -%}{{ hs_head }} enlaza a <a href="{{ hs_bad.url | relative_url }}"><code>{{ hs_bad.url }}</code></a>, que no cuelga de <code>/{{ hs_sec }}/</code></li>{%- endcapture -%}
      {%- assign hs_fm_wrong = hs_fm_wrong | append: hs_row -%}
    {%- else -%}
      {%- assign hs_n_none = hs_n_none | plus: 1 -%}
      {%- capture hs_row -%}{{ hs_head }}</li>{%- endcapture -%}
      {%- assign hs_fm_none = hs_fm_none | append: hs_row -%}
    {%- endif -%}
  {%- endfor -%}
{%- endfor -%}
{%- capture hs_out_fm -%}
{%- if hs_n_none == 0 and hs_n_wrong == 0 -%}
Todo OK.
{%- else -%}
{%- if hs_n_none > 0 %}
<details open>
<summary><b>No existe ninguna pagina con ese titulo</b> — {{ hs_n_none }}</summary>
<p>La ficha los dibuja como texto pelado, sin link.</p>
<ul>{{ hs_fm_none }}</ul>
</details>
{% endif %}
{%- if hs_n_wrong > 0 %}
<details open>
<summary><b>Resuelve en la seccion equivocada</b> — {{ hs_n_wrong }}</summary>
<p>Peor que no resolver: la ficha enlaza a la pagina <b>incorrecta</b> y no se
nota. Ver <code>wc_fields</code> en <code>wiki_card.html</code>.</p>
<ul>{{ hs_fm_wrong }}</ul>
</details>
{% endif %}
{%- endif -%}
{% endcapture %}


{%- comment -%}
  ======================================================================
  4. Huerfanas, detras de bandera
  ======================================================================

  site.health_orphans, en _config_local.yml. Liquid renderiza solo la rama
  verdadera de un If, asi que con la bandera apagada esto no cuesta nada --
  siempre y cuando TODO assign caro viva adentro del if, no arriba.

  Cuesta mucho menos de lo que parece. backlinks.html es caro porque son 206
  paginas RENDERIZADAS x 206 barridas; esta pagina se renderiza una sola vez,
  asi que arranca en 1/206 de aquello. Ademas se arma un unico pajar concatenado
  (una sola pasada de Ruby sobre ~800 KB) y el barrido queda en ~195 vueltas de
  Liquid haciendo un String#include? cada una.

  El pajar se arma con hs_scan y NO con site.pages: characters/index.md
  renderizado enlaza a los 59 personajes mientras que crudo no enlaza a ninguno,
  asi que incluirlo haria que la lista cambiara entre builds.

  Segundo canal: el front matter. Un NPC con `location: Safepoint` enlaza a
  Safepoint desde la ficha, que vive en el layout y por lo tanto nunca esta en
  content. Esos valores se juntan en strings por seccion y se consultan solo
  contra los destinos de la seccion que les corresponde, que conserva la guarda
  de seccion sin costo.

  Los diez index.md quedan exentos solos: no tienen `parent:`, asi que el filtro
  de abajo no los incluye. Nueve de ellos son huerfanos por construccion.
{%- endcomment -%}
{%- capture hs_out_orph -%}
{%- if site.health_orphans -%}

  {%- assign hs_hay = hs_scan | map: "content" | join: " " -%}
  {%- capture hs_fm_loc -%}|{{ site.pages | map: "world" | join: "|" }}|{{ site.pages | map: "continent" | join: "|" }}|{{ site.pages | map: "region" | join: "|" }}|{{ site.pages | map: "settlement" | join: "|" }}|{{ site.pages | map: "location" | join: "|" }}|{{ site.pages | map: "seat" | join: "|" }}|{%- endcapture -%}
  {%- capture hs_fm_chr -%}|{{ site.pages | map: "holder" | join: "|" }}|{{ site.pages | map: "leader" | join: "|" }}|{%- endcapture -%}
  {%- capture hs_fm_fac -%}|{{ site.pages | map: "faction" | join: "|" }}|{%- endcapture -%}
  {%- capture hs_fm_lor -%}|{{ site.pages | map: "pantheon" | join: "|" }}|{%- endcapture -%}

  {%- assign hs_orph_total = 0 -%}
  {%- assign hs_orph_body = "" -%}
  {%- for hs_sec in hs_secs -%}
    {%- assign hs_kids = site.pages | where: "parent", hs_sec | sort: "title" -%}
    {%- assign hs_rows = "" -%}
    {%- assign hs_n = 0 -%}
    {%- for hs_t in hs_kids -%}
      {%- comment -%}
        Se busca la url pelada (/locations/settlements/verna.html), que es
        substring de la forma con baseurl que el plugin realmente escribe: anda
        con baseurl y sin el. Mismo criterio que backlinks.html.
      {%- endcomment -%}
      {%- if hs_hay contains hs_t.url -%}{%- continue -%}{%- endif -%}
      {%- capture hs_needle -%}|{{ hs_t.title }}|{%- endcapture -%}
      {%- if hs_t.url contains "/locations/" and hs_fm_loc contains hs_needle -%}{%- continue -%}{%- endif -%}
      {%- if hs_t.url contains "/characters/" and hs_fm_chr contains hs_needle -%}{%- continue -%}{%- endif -%}
      {%- if hs_t.url contains "/factions/" and hs_fm_fac contains hs_needle -%}{%- continue -%}{%- endif -%}
      {%- if hs_t.url contains "/lore/" and hs_fm_lor contains hs_needle -%}{%- continue -%}{%- endif -%}
      {%- assign hs_n = hs_n | plus: 1 -%}
      {%- capture hs_row -%}<li><a href="{{ hs_t.url | relative_url }}">{{ hs_t.title }}</a> <code class="loc-todo">{{ hs_t.path }}</code></li>{%- endcapture -%}
      {%- assign hs_rows = hs_rows | append: hs_row -%}
    {%- endfor -%}
    {%- if hs_n > 0 -%}
      {%- assign hs_orph_total = hs_orph_total | plus: hs_n -%}
      {%- capture hs_orph_body -%}{{ hs_orph_body }}
<details>
<summary><b>{{ hs_sec }}</b> — {{ hs_n }} de {{ hs_kids.size }}</summary>
<ul>{{ hs_rows }}</ul>
</details>
{% endcapture -%}
    {%- endif -%}
  {%- endfor -%}

  {%- if hs_orph_total == 0 -%}
Todo OK.
  {%- else -%}
**{{ hs_orph_total }} paginas** no estan enlazadas desde ningun cuerpo ni desde
ninguna ficha. No todas son un error ---una sesion sin nada memorable puede no
ser nombrada nunca--- pero una ubicacion o un item si suele serlo.
{{ hs_orph_body }}
  {%- endif -%}
{%- else -%}
Apagado. Para verlo, `health_orphans: true` en `_config_local.yml`; Jekyll
vigila los archivos que le pasan por `--config` y se reinicia solo.
{%- endif -%}
{% endcapture %}


{%- comment -%}
  De aca para abajo, markdown y nada mas: ni un if, ni un for, ni un recorte de
  espacios. Ver "por que la cuenta va toda arriba" en el encabezado.
{%- endcomment -%}

# Salud del wiki

Pagina local de mantenimiento: lo que esta a medio cargar y no se nota mientras
se escribe. No se publica ---ver el comentario al principio del fuente--- asi que
no hay que cuidarse de lo que diga.

Se miran por dentro {{ hs_scan.size }} paginas.

## Sin `summary:`

{{ hs_out_sum }}

## Sesiones

{{ hs_out_sess }}

## Referencias rotas

### Links `.md` muertos

{{ hs_out_dead }}

### Front matter que no resuelve

{{ hs_out_fm }}

## Paginas que nadie enlaza

{{ hs_out_orph }}
