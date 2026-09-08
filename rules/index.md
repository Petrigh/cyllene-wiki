---
title: House Rules
nav_order: 10
has_children: true
---

# House Rules

Reglas que hemos decidido sobre la mesa.

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

