---
title: The Party
parent: Characters
nav_order: 1
has_children: false
summary: Quien se sienta en la mesa
has_toc: false
---

# The Party

Roster, esto es mas para estar al tanto de que es capaz el equipo para tomar decisiones en el proximo combate.

{% assign pcs = site.pages | where: "parent", page.title | sort: "title" %}

| Character | Player | Class & level | Passive Perception | Languages |
|---|---|---|---|---|
{% for pc in pcs %}| [{{ pc.title }}]({{ pc.url | relative_url }}) | {{ pc.player | default: "—" }} | {{ pc.class | default: "—" }} | {{ pc.passive_perception | default: "—" }} | {{ pc.languages | default: "—" }} |
{% endfor %}

## Recursos

- **Curaciones disponibles por dia:** 2 × *cure wounds*
- **Fondos:** X gp, lo tiene todo [Iri](party/iri.md)

## Orden de formacion

Frente: — · Medio: — · Detras: —

## Leyes que se imparten al grupo

Reglas que el grupo acordo a seguir.

- No se acepta absolutamente nada de las feys.
- [Denzen](party/denzen.md) no puede saber donde esta la [muñeca](../items/muneca_ethel.md).
