---
title: "Template — Faction"
parent: Templates
nav_order: 4
---

# Faction template

Copy into `factions/`.

---

```yaml
---
title: The Ashen Compact
parent: Factions
summary: Salvagers with a monopoly on anything pulled from the burn scar
standing: Wary
leader: Marrow Quillane
seat: Greyfen
members: Unos cuarenta, mas los que compran
status: Activa
---
```

## The side card

Every page under `factions/` gets a card in the right-hand column, built from
the frontmatter above — no include to add, it is automatic.

- `leader` and `seat` turn into links when they match another page's `title:`
  exactly, so the faction points at its boss and its base.
- `members` is one line, not a list — the column is narrow.
- `standing` is the same value the table below explains, shown as
  **Con la party**.
- The image comes from `assets/img/`, matched on the filename:
  `warlock_motors.md` picks up `assets/img/Warlock Motors.jpg`. Spaces,
  hyphens and case do not matter. Anything else needs `image:` spelled out.

Same card on characters, locations and items — the full field list is in
[the side card reference](card.md).

## Standing with the party

**Wary.** Moves up when the party brings them salvage they could have sold
elsewhere. Moves down every time they are seen with the Watch.

| Level | What it gets you |
|---|---|
| Hostile | Doors close, prices double |
| Wary | Business only, cash first |
| Trusted | Credit, and they answer questions |
| Sworn | They will spend people on your problem |

## What they want

The goal they would sacrifice for. One sentence, no hedging.

## How they get it

Their methods, which is what makes them a threat or an ally.

## What they have

- **People:**
- **Money:**
- **Reach:**
- **Weakness:**

## Who to talk to

| Name | Role | Where |
|---|---|---|
| [NPC](../characters/) | | |

## Current agenda

A progress clock. Fill a segment each session the party does not interfere.

`[ ] [ ] [ ] [ ] [ ] [ ]` — *When full:* what happens to the world.

## Rivals

Who wants them gone, and why.
