---
title: Locations
nav_order: 3
has_children: false
has_toc: false
---

# Locations

Lugares que la party a visitado, o tiene informacion al respecto.

{% assign all         = site.pages | where: "parent", page.title | sort: "title" %}
{% assign settlements = all | where: "kind", "settlement" %}
{% assign buildings   = all | where: "kind", "building" %}
{% assign nature      = all | where: "kind", "nature" %}
{% assign regions     = all | where: "kind", "region" %}
{% assign known       = "settlement,building,nature,region" | split: "," %}

## Settlements

Pueblos, ciudades y campamentos.

{% if settlements.size > 0 %}
<ul>
{% for kid in settlements %}
  <li><a href="{{ kid.url | relative_url }}">{{ kid.title }}</a>{% if kid.summary %} — {{ kid.summary }}{% endif %}</li>
{% endfor %}
</ul>
{% else %}
Aun no se han agregado.
{% endif %}

## Buildings

{% if buildings.size > 0 %}
<ul>
{% for kid in buildings %}
  <li><a href="{{ kid.url | relative_url }}">{{ kid.title }}</a>{% if kid.summary %} — {{ kid.summary }}{% endif %}</li>
{% endfor %}
</ul>
{% else %}
Aun no se han agregado.
{% endif %}

## Natural Locations

{% if nature.size > 0 %}
<ul>
{% for kid in nature %}
  <li><a href="{{ kid.url | relative_url }}">{{ kid.title }}</a>{% if kid.summary %} — {{ kid.summary }}{% endif %}</li>
{% endfor %}
</ul>
{% else %}
Aun no se han agregado.
{% endif %}

## Regions

{% if regions.size > 0 %}
<ul>
{% for kid in regions %}
  <li><a href="{{ kid.url | relative_url }}">{{ kid.title }}</a>{% if kid.summary %} — {{ kid.summary }}{% endif %}</li>
{% endfor %}
</ul>
{% else %}
Aun no se han agregado.
{% endif %}

{% assign otros = 0 %}
{% for kid in all %}{% unless known contains kid.kind %}{% assign otros = otros | plus: 1 %}{% endunless %}{% endfor %}
{% if otros > 0 %}

## Sin clasificar

<ul>
{% for kid in all %}{% unless known contains kid.kind %}
  <li><a href="{{ kid.url | relative_url }}">{{ kid.title }}</a>{% if kid.summary %} — {{ kid.summary }}{% endif %}</li>
{% endunless %}{% endfor %}
</ul>
{% endif %}
