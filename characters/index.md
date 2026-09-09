---
title: Characters
nav_order: 2
has_children: true
has_toc: false
---

# Characters

Lista de personajes. Arriba los PCs, debajo el resto de NPCs.

{% assign pcs  = site.pages | where: "parent", "The Party" | sort: "title" %}
{% assign npcs = site.pages | where: "parent", page.title | where: "type", "npc" | sort: "title" %}

## The Party

Roster, recursos y leyes del grupo en [The Party]({{ "/characters/party.html" | relative_url }}).

{% if pcs.size > 0 %}
<ul>
{% for kid in pcs %}
  <li><a href="{{ kid.url | relative_url }}">{{ kid.title }}</a>{% if kid.summary %} — {{ kid.summary }}{% endif %}</li>
{% endfor %}
</ul>
{% else %}
Aun no se han agregado PCs.
{% endif %}

## NPCs

{% if npcs.size > 0 %}
<ul>
{% for kid in npcs %}
  <li><a href="{{ kid.url | relative_url }}">{{ kid.title }}</a>{% if kid.summary %} — {{ kid.summary }}{% endif %}</li>
{% endfor %}
</ul>
{% else %}
Aun no se han agregado NPCs.
{% endif %}
