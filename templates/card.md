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
| `kind` | Tipo | locations, bestiary, factions | Spanish in the file, shown capitalised |
| `race` | Raza | characters | |
| `subrace` | Subraza | characters | only when the race has one |
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
grades a guess column by column against the answer. Two of its five scored
columns come straight from the frontmatter above — filling them in makes the
game sharper *and* fills in the card, since they are the same keys.

| Column | Key | Where it applies |
|---|---|---|
| Tipo | `race` on characters, `kind` on everything else | all |
| Region | `location` on characters, `settlement`/`region`/`continent`/`world` on places, `seat` on factions | all |

The other three — **Categoria**, **1a aparicion** and **Sesiones** — are
derived, not written: the game counts which session pages link the entity.
Nothing to fill in there; just link things from the session logs as usual.

`faction` and `status` used to be columns and no longer are: `faction` is set
on under half the entities so it was almost always grey, and `status` is `Vivo`
on nearly all the rest so it was almost always green. A column that gives the
same colour whatever you guess rules nothing out. The reasoning is in the
header of `_includes/cylledle.html`; both still show on the card.

`subrace` is **not** a column either, for the same reason — seven entries
carry one, so it would be grey almost every day. It only shows on the card.

A key left out is **not** an error. The game paints that cell grey and does not
score it, which is the honest answer for something the wiki has not said yet.
Guessing a value to fill the grid would show the table a wrong answer as canon.

### `kind:` values

Spanish, lowercase, no accents, and shown just capitalised — there is no
translation step. The vocabulary is [`_data/kinds.yml`](../_data/kinds.yml),
and that one file is read by the Locations tree, the side card, the hover
preview, the Cylledle board and the health-page lint. Adding a kind means
adding one line there and nothing else.

| Section | Values |
|---|---|
| `locations/` | `mundo` `continente` `region` `asentamiento` `edificacion` `naturaleza` |
| `bestiary/` | `aberracion` `bestia` `no-muerto` `planta` `constructo` `humanoide` `feerico` `monstruosidad` |
| `factions/` | `orden` `banda` `consejo` `escuela` `familia` `party` |

Use a value that is not in that list and two things tell you: the page lands in
the **Otros** bucket of the Locations tree, and the health page lists it. Both
are visible, which matters because everything else about `kind` fails silently.

**`kind` is not free text.** It groups the Locations tree
(`_includes/location_children.html`), seeds its roots
(`locations/index.md`) and colours the map pins (`[data-kind=…]` in
`_sass/custom/custom.scss`). Mistype one and nothing errors — the page just
quietly stops being where it should be.

The location **keys** (`settlement:`, `region:`, `continent:`, `world:`) are a
different thing and stay in English — see
[the Location template](location.md).

### `race:` and `subrace:` values

The opposite rule to `kind`: nothing links or groups by race, so it is written
in Spanish directly in the file. It is only ever **compared** — by the card,
which prints it as-is, and by Cylledle, which matches without accents or case
but has no dictionary. `Elf` and `Elfo` are the same race and the board scored
them red, which is why the vocabulary is closed:

| | Values |
|---|---|
| Translated | `Elfo` `Enano` `Gnomo` `Humano` `Semielfo` `Diablo` |
| Kept as-is | `Tiefling` `Halfling` `Aasimar` `Goblin` `Satyr` |
| Homebrew | `Goatkin` `Owling` |

Masculine singular whatever the character'"'"'s gender — it is the species, not
the person, and the column has to compare. The health page lists anything else.

`subrace:` takes the qualifier that used to be glued to the race, so that two
elves score green on Tipo and the detail survives on the card:

| `race` | `subrace` |
|---|---|
| `Elfo` | `Alto` `Del bosque` |
| `Enano` | `De la colina` |
| `Tiefling` | `Levistus` |
| `Goatkin` | `De montaña` |

It is open-ended and not linted — add one when the race has a real variant,
leave it out otherwise. `Semielfo` is a race of its own in 5e, not an elf
subrace.

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
