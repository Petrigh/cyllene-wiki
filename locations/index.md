---
title: Locations
nav_order: 3
has_children: false
has_toc: false
---

# Locations

Lugares que la party a visitado, o tiene informacion al respecto.

{% assign all = site.pages | where: "parent", page.title %}
{% assign worlds = all | where: "kind", "world" | sort: "title" %}

{% if worlds.size > 0 %}
<ul class="loc-tree">
{% for w in worlds %}
  {% include location_item.html page=w depth=0 %}
{% endfor %}
</ul>

<script>
// Los botones se inyectan desde JS: sin JS no sirven de nada, y una lista
// plegable ya funciona sola (<details> es nativo).
(function () {
  var tree = document.querySelector('.loc-tree');
  if (!tree) return;
  var all = tree.querySelectorAll('details');
  if (!all.length) return;

  var bar = document.createElement('p');
  bar.className = 'loc-controls';

  [['Expandir todo', true], ['Contraer todo', false]].forEach(function (pair) {
    var b = document.createElement('button');
    b.type = 'button';
    b.textContent = pair[0];
    b.addEventListener('click', function () {
      tree.querySelectorAll('details').forEach(function (d) { d.open = pair[1]; });
    });
    bar.appendChild(b);
  });

  tree.parentNode.insertBefore(bar, tree);
})();
</script>
{% else %}
Aun no se han agregado.
{% endif %}

{%- comment -%}
  Red de seguridad: paginas que no cuelgan de ningun lugar existente. Hoy no hay
  ninguna, asi que la seccion entera no se imprime — pero si algun dia se carga
  una pagina sin clave de contenedor, o apuntando a un titulo mal escrito,
  aparece aca en vez de desaparecer del arbol de arriba.
{%- endcomment -%}
{% assign titles = all | map: "title" %}
{% capture loose %}
{%- for p in all -%}
  {%- unless p.kind == "world" -%}
    {%- assign key = p.settlement | default: p.region | default: p.continent | default: p.world -%}
    {%- if key == nil or key == "" %}
      <li><a href="{{ p.url | relative_url }}">{{ p.title }}</a> — sin lugar asignado</li>
    {%- else -%}
      {%- unless titles contains key %}
      <li><a href="{{ p.url | relative_url }}">{{ p.title }}</a> — apunta a <em>{{ key }}</em>, que no existe</li>
      {%- endunless -%}
    {%- endif -%}
  {%- endunless -%}
{%- endfor -%}
{% endcapture %}
{% assign loose_trimmed = loose | strip %}

{% if loose_trimmed != "" %}
## Sin ubicar

Estas paginas no cuelgan de ningun lugar existente. Agregales un `world:`,
`continent:`, `region:` o `settlement:` que coincida con el titulo exacto de
otra pagina.

<ul>{{ loose }}</ul>
{% endif %}
