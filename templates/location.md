---
title: "Template — Location"
parent: Templates
nav_order: 3
---

# Location template

Copy into the subfolder that matches the kind:

| `kind:` | Folder | For |
|---|---|---|
| `asentamiento` | `locations/settlements/` | Towns, cities, camps |
| `edificacion` | `locations/buildings/` | Chapels, inns, towers, a single structure |
| `naturaleza` | `locations/nature/` | Forests, caves, rivers, mountains |
| `region` | `locations/regions/` | Large territories holding the above |
| `continente` | `locations/continentes/` | Continents inside a world |
| `mundo` | `locations/` | The world itself — the root of the tree |

The folder names are still English and the `kind:` values are Spanish. That is
not a mistake waiting to be tidied: **nothing reads the folder path.** The
folder is where you find the file; `kind:` is what the site groups on.

`parent:` stays `Locations` whichever folder you use — `kind:` is what sorts the
page into its section on the Locations index.

## Where the page hangs from

Add **one** key naming the place that contains this one, matching its `title:`
exactly:

| Key | Names a page of kind |
|---|---|
| `settlement:` | `asentamiento` |
| `region:` | `region` |
| `continent:` | `continente` |
| `world:` | `mundo` |

**The keys stay in English, the values are in Spanish.** They are two different
things that happen to share a word: `region:` is a *field name* the site filters
on, `region` is a *kind value*. Translating a key would detach every page that
uses it from the tree, so only the values moved.

A page may hang off **any** level above it, not just the one immediately above.
That is deliberate, and the index handles it: a roaming dungeon can hang off the
continent (`Shady Elmer's Fun Emporium` does), a distant kingdom off the world
(`Aira`), a temple in the open off a region (`Templo de Gaia`). The index asks
each place "which pages name me?" regardless of their `kind`, so the page shows
up under whatever it points at.

Only a `mundo` page carries no such key — it is the root.

## `status:`

Optional, and written **only when something happened** to the place:
`En pie` `Destruido` `Tomado` `Abandonado` `Perdido`. A town the wiki never
says anything about is left blank — see [the side card reference](card.md).

If the key is missing, or names a title that does not exist, the page is not
lost: it shows up under **Sin ubicar** at the bottom of the Locations index.

To pin the place on the home-page map, add `map_x` / `map_y` (percent from the
top-left corner of the image). Open the site with `?pick` on the URL, click the
spot, and it hands you the two lines to paste.

---

```yaml
---
title: Greyfen
parent: Locations
summary: Fen-side town of two thousand, built on a drained lake
kind: asentamiento
region: The Sallowmarch
status: Tomada por los paladines
facts:
  - El unico puente cruza por la muralla
---
```

## The side card

Every page under `locations/` gets a card in the right-hand column, built from
the frontmatter above — no include to add, it is automatic.

- `kind` shows up as **Tipo**, capitalised (the value is already in Spanish);
  whichever of `settlement:`, `region:`, `continent:` or `world:` the page hangs
  from becomes a link back to it.
- `status`, `facts:` and an image named after the file (`whiterun.md` ->
  `assets/img/Whiterun.jpg`) round it out.
- `summary` doubles as the caption under the image.

Same card on characters, factions and items — the full field list is in
[the side card reference](card.md).

## In a line

What the place is for, in the story. "The last safe bed before the marsh."

## Arriving

Write for reading aloud. Three senses, no more than four sentences.

- **See:**
- **Hear:**
- **Smell:**

## Who runs it

| | |
|---|---|
| Authority | |
| Real power | |
| Population | |
| Wealth | |
| Attitude to strangers | |

## Worth visiting

| Place | Why the party would go | Who is there |
|---|---|---|
| | | |

## Rumours

Roll d6 or pick. Mark each one true, false, or twisted — the party never sees this column.

| d6 | Rumour | |
|---|---|---|
| 1 | | true |
| 2 | | twisted |

## Getting there

From where, how long, and what the road costs.

## Complications

Two or three things that could go wrong while the party is here.

<div class="spoiler" markdown="1">
**DM only — do not publish.** What is actually going on underneath, and the
clue that lets the party find it.
</div>
