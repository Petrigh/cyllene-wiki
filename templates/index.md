---
title: Templates
nav_order: 11
has_children: true
---

# Templates

Copy a template into the right folder, rename it, fill it in. Delete the prompts as you go.

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

New page? Copy [one of these](../templates/).
