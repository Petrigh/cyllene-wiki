---
title: "Template — NPC"
parent: Templates
nav_order: 1
---

# NPC template

Copy this file into `characters/`, rename it to the character's name in
lowercase-with-hyphens, and change `parent: Templates` to `parent: Characters`.

---

## Frontmatter to use

```yaml
---
title: Marrow Quillane
parent: Characters
type: npc
summary: Undertaker in Greyfen who knows which graves are empty
race: Human
role: Undertaker
status: Alive
faction: None
location: Greyfen
attitude: Wary
facts:
  - Buried the last magistrate, and will not say where
---
```

## The side card

Every page under `characters/` gets a card in the right-hand column, built
from the frontmatter above — no include to add, it is automatic.

- `race`, `role`, `status`, `faction`, `location`, `attitude` become the
  bullets, in that order. Leave out whatever you do not know yet.
- `faction` and `location` turn into links when the value matches another
  page's `title` exactly. Otherwise they stay plain
  text, so a wrong value never breaks the build.
- `facts:` is a list of free bullets for anything the fields above do not
  cover. Keep them to one line each — the column is narrow.
- The portrait comes from `assets/pjs/`, matched on the filename: a page at
  `characters/NPCs/gareth.md` picks up `assets/pjs/Gareth.jpeg`. Case and
  extension do not matter. To point somewhere else, set
  `portrait: /assets/pjs/otro.jpeg`, and `portrait_alt:` for the alt text.
- `summary` doubles as the caption under the portrait.

A page with no portrait and none of these fields renders exactly as before.

## One breath

How you play them the moment they walk on: voice, posture, and what they want
out of this conversation. One sentence. This is the only line the DM re-reads.

## Quick facts

| | |
|---|---|
| Ancestry / kind | |
| Does what | |
| Lives where | |
| Faction | |
| Status | Alive / Dead / Missing / Unknown |
| Feeling about the party | Warm / Neutral / Wary / Hostile — and why |

## First impression

- **You notice** — one physical detail, not a full portrait.
- **They sound like** — accent, pace, a word they overuse.
- **They keep doing** — the mannerism you can repeat for recognition.

## Wants, fears, won't

- **Wants:** the thing they would take a risk for.
- **Fears:** the thing that makes them lie.
- **Won't:** the line they will not cross, even for money.

## What the party knows

Dated, so the page reflects the party's understanding rather than the truth.

- *Session 3* — Told the party the crypt has been sealed for forty years.

## Connections

- Serves [Faction](../factions/) as …
- Owes [Someone](../characters/) a …
- Can be found at [Place](../locations/)

## Heard at the table

> A line worth remembering, and the session it happened in.

## If it comes to a fight

Statblock: **Commoner** (MM p. 345), plus proficiency in Insight. Note only
the changes, not the whole block.

<div class="spoiler" markdown="1">
**DM only — do not publish.** Move this section to a page under `dm/` if the
site is public. What they are hiding, who they really work for, and the die
roll or trigger that reveals it.
</div>
