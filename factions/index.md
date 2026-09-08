---
title: Factions
nav_order: 4
has_children: true
---

# Factions

Cada grupo u organizacion que desea algo y es capaz de actuar para conseguirlo.

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
