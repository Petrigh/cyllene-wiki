---
title: Characters
nav_order: 2
has_children: true
---

# Characters

Lista de personajes, al principio se encuentran los PCs, y debajo el resto de NPCs

{% assign kids = site.pages | where: "parent", page.title | sort: "title" %}
{% if kids.size > 0 %}
<ul>
{% for kid in kids %}
  <li><a href="{{ kid.url | relative_url }}">{{ kid.title }}</a>{% if kid.summary %} — {{ kid.summary }}{% endif %}</li>
{% endfor %}
</ul>
{% else %}
Aun no se han agregado.
{% endif %}

