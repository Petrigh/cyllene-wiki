---
title: Quests
nav_order: 6
has_children: true
---

# Quests

Open threads. A quest leaves this list only when the party knows it is finished.

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

New page? Copy [the quest template](../templates/).
