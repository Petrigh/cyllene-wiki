---
title: House Rules
nav_order: 10
has_children: true
---

# House Rules

Rulings we made at the table and intend to keep. Dated, so we can tell when we changed our minds.

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
