---
title: "Reference — The side card"
parent: Templates
nav_order: 0
summary: The image-and-facts box in the right-hand column, and every field it reads
---

# The side card

Pages under `characters/`, `locations/`, `factions/` and `items/` get a card in
the right-hand column, built from the frontmatter — there is no include to add,
it is automatic. It is one include (`_includes/wiki_card.html`) and one layout
(`_layouts/wiki.html`) shared by all four sections; `_config.yml` wires them up.

A page with no image and none of the fields below renders exactly as if the
card did not exist, so the section `index.md` pages are unaffected.

## The image

Drop a file in the section's image folder named after the `.md` file and it
shows up on its own:

| Section | Folder | Example |
|---|---|---|
| `characters/` | `assets/pjs/` | `NPCs/gareth.md` → `Gareth.jpeg` |
| `locations/` | `assets/img/` | `settlements/whiterun.md` → `Whiterun.jpg` |
| `factions/` | `assets/img/` | `warlock_motors.md` → `Warlock Motors.jpg` |
| `items/` | `assets/img/` | `van.md` → `Van.png` |

Case, extension, and whether the words are separated by spaces, hyphens or
underscores do not matter — `Warlock Motors.jpg` matches `warlock_motors.md`.
Anything else needs the name spelled out:

```yaml
image: /assets/img/Parche Indeseables de Brolwund.jpg
image_alt: Parche de los Indeseables      # default: the page title
```

`summary:` doubles as the caption under the image.

## The fields

Each one is drawn only if the page has it, so the list below is the union of
all four sections and every page shows its own. They come out in this order,
whichever ones are present:

| Key | Label | Used by | |
|---|---|---|---|
| `aliases` | Alias | characters | see below |
| `kind` | Tipo | locations | shown in Spanish; stays in English in the file |
| `race` | Raza | characters | |
| `class` | Clase | characters | |
| `player` | Jugador | characters | |
| `role` | Rol | characters | |
| `rarity` | Rareza | items | |
| `attunement` | Sintonizacion | items | `true` / `false` → Si / No |
| `holder` | Portador | items | links |
| `leader` | Lider | factions | links |
| `seat` | Sede | factions | links |
| `members` | Miembros | factions | one line, not a list |
| `pantheon` | Panteon | characters | links |
| `faction` | Faccion | characters | links |
| `settlement` | En | locations | links |
| `region` | Region | locations | links |
| `continent` | Continente | locations | links |
| `world` | Mundo | locations | links |
| `location` | Donde | characters | links |
| `status` | Estado | any | |
| `standing` | Con la party | factions | |
| `attitude` | Con la party | characters | |

**links** means the value turns into a link when it matches another page's
`title:` exactly. Otherwise it stays plain text, so a wrong value never breaks
the build — it just does not link.

A value that is only dashes (`--`, the placeholder for "not filled in yet") is
skipped, the same as leaving the key out.

To add a field, add one `clave|Etiqueta|link` entry to `wc_fields` in
`_includes/wiki_card.html`. Nothing else needs to change.

## `aliases` and `facts`

```yaml
aliases:                            # otros nombres; el que repite el titulo
  - Gary                            # de la pagina se ignora
  - name: Obeon                     # con link: la url de la pagina donde
    link: /sessions/18.html         #   aparece ese nombre
facts:                              # bullets libres, para lo que no entra arriba
  - Hermano de Gaia                 # una linea cada uno: la columna es angosta
  - Le debe un favor a la party
```

`facts:` always goes last.

## What Cylledle reads

The daily puzzle ([`cylledle.md`](../cylledle.md), `_includes/cylledle.html`)
grades a guess column by column against the answer. Four of its seven columns
come straight from the frontmatter above — filling them in makes the game
sharper *and* fills in the card, since they are the same keys.

| Column | Key | Where it applies |
|---|---|---|
| Naturaleza | `race` on characters, `kind` on everything else | all |
| Afiliacion | `faction` | mostly characters |
| Region | `location` on characters, `settlement`/`region`/`continent`/`world` on places, `seat` on factions | all |
| Estado | `status` | all |

The other three columns — **Seccion**, **1a aparicion** and **N de sesiones** —
are derived, not written: the game counts which session pages link the entity.
Nothing to fill in there; just link things from the session logs as usual.

A key left out is **not** an error. The game paints that cell grey and does not
score it, which is the honest answer for something the wiki has not said yet.
Guessing a value to fill the grid would show the table a wrong answer as canon.

### `kind:` values

Stored in English and lowercase, shown translated (see `wc_kinds` in
`_includes/wiki_card.html`). Only the `locations` set groups the Locations tree;
the other two just label the page and feed the game.

| Section | Values |
|---|---|
| `locations/` | `world` `continent` `region` `settlement` `building` `nature` |
| `bestiary/` | `aberration` `beast` `undead` `plant` `construct` `humanoid` `fey` `monstrosity` |
| `factions/` | `order` `gang` `council` `school` `family` `party` |

### `status:` values

Free text, but keep to these so two pages meaning the same thing score as equal
— the game compares without accents or case, yet `Vivo` and `Viva` share no word
and would read as different answers.

| Section | Values |
|---|---|
| characters, bestiary | `Vivo` `Muerto` `Atrapado` `Desaparecido` |
| `locations/` | `En pie` `Destruido` `Tomado` `Abandonado` `Perdido` |
| `factions/` | `Activa` `Disuelta` `Latente` |

Use the masculine singular for people and creatures whatever their gender —
it is the species/state, not the person, and the column has to compare.

On locations, `status:` is written **only when something happened**. A town the
wiki never says anything about is left blank rather than marked `En pie`: a
column where fifty of fifty-six pages say the same thing tells nobody anything.

### `faction:` is one value

`wiki_card` links it, so it takes a single name, not a list — a list gets
concatenated into one string and stops resolving (the health page catches this).
If someone belongs to two, put the defining one here and leave the rest to the
body text.
