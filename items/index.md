---
title: Items
nav_order: 6
has_children: false
has_toc: false
---

# Items

Items magicos, contratos, llaves, o cualquier elemento que la party haya deliberado que hay un portador designado.

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
