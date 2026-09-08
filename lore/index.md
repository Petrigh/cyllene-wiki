---
title: Lore
nav_order: 9
has_children: true
---

# Lore

The world behind the adventure: history, gods, calendar, languages.

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

New page? Copy [any template](../templates/).
