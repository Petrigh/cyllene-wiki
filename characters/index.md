---
title: Characters
nav_order: 2
has_children: true
---

# Characters

Everyone with a name and a face. Party members first, then anyone the party has spoken to for longer than a sentence.

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

New page? Copy [the PC or NPC template](../templates/).
