---
title: Bestiary
nav_order: 9
has_children: false
has_toc: false
---

# Bestiary

Criaturas que la party enfrento, estudio o fue avisada acerca.

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

