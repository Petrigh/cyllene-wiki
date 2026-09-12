---
title: "Template — Location"
parent: Templates
nav_order: 3
---

# Location template

Copy into the subfolder that matches the kind:

| `kind:` | Folder | For |
|---|---|---|
| `settlement` | `locations/settlements/` | Towns, cities, camps |
| `building` | `locations/buildings/` | Chapels, inns, towers, a single structure |
| `nature` | `locations/nature/` | Forests, caves, rivers, mountains |
| `region` | `locations/regions/` | Large territories holding the above |
| `continent` | `locations/continentes/` | Continents inside a world |
| `world` | `locations/` | The world itself — the root of the tree |

`parent:` stays `Locations` whichever folder you use — `kind:` is what sorts the
page into its section on the Locations index.

## Where the page hangs from

Add **one** key naming the place that contains this one, matching its `title:`
exactly:

| Key | Names a page of kind |
|---|---|
| `settlement:` | `settlement` |
| `region:` | `region` |
| `continent:` | `continent` |
| `world:` | `world` |

A page may hang off **any** level above it, not just the one immediately above.
That is deliberate, and the index handles it: a roaming dungeon can hang off the
continent (`Shady Elmer's Fun Emporium` does), a distant kingdom off the world
(`Aira`), a temple in the open off a region (`Templo de Gaia`). The index asks
each place "which pages name me?" regardless of their `kind`, so the page shows
up under whatever it points at.

Only a `world` page carries no such key — it is the root.

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
kind: settlement
region: The Sallowmarch
---
```

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
