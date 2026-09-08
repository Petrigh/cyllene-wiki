---
title: Locations
nav_order: 3
has_children: true
---

# Locations

Places the party has been, or been told about. A location earns a page once it has a name and one interesting thing in it.

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

New page? Copy [the location template](../templates/).
