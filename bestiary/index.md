---
title: Bestiary
nav_order: 7
has_children: true
---

# Bestiary

Creatures the party has fought, studied, or been warned about. Record what the party learned, not the full stat block.

{% assign kids = site.pages | where: "parent", page.title | sort: "title" %}
{% if kids.size > 0 %}
<ul>
{% for kid in kids %}
  <li><a href="{{ kid.url | relative_url }}">{{ kid.title }}</a>{% if kid.summary %} — {{ kid.summary }}{% endif %}</li>
{% endfor %}
</ul>
{% else %}
Nothing here yet.
{% endif %}

New page? Copy [the creature template](../templates/).
