# D&D campaign wiki template

Markdown files that work as **a Notion wiki now** and **a published GitHub Pages
site later**, without rebuilding anything in between.

Why Markdown and not a Notion export: Notion's HTML export produces hashed
filenames, broken internal links, and no database views, so it makes a poor
static site. Notion *imports* Markdown and CSV cleanly, and GitHub Pages
*renders* Markdown natively. Markdown is the format both ends agree on.

## What's here

```
index.md            Wiki home
characters/         The party + NPCs
locations/          Settlements, dungeons, regions
factions/           Groups with goals, and party standing
sessions/           One page per game night
quests/             Open threads
bestiary/           Creatures, as the party knows them
items/              Magic items and plot objects
lore/               Timeline, history, gods
rules/              House rules and table logistics
templates/          Copy these when adding a page
dm/                 Spoilers — excluded from the site (read dm/README.md)
notion-csv/         Same structure as CSV, for Notion databases
_config.yml         GitHub Pages settings
_sass/              Colour scheme and small style overrides
```

Every section has an `index.md` that lists its own pages automatically. Add a
file with the right `parent:` in its frontmatter and it appears in the sidebar
and in the section list — no index to maintain.

## Use it in Notion

**Option A — pages (keeps the writing).**
1. Zip this folder, or use the zip you downloaded.
2. In Notion: **Settings → Import → Markdown & CSV**, upload the zip.
3. Notion recreates the folder structure as nested pages.
4. Delete the `---` frontmatter blocks that appear at the top of imported pages;
   Notion shows them as plain text. Turn those fields into Notion properties if
   you want to filter by them.
5. The template-tag lines on `index.md` pages are site-only —
   delete them in Notion and use a linked database view instead.

**Option B — databases (keeps the filtering).**
Import the files in `notion-csv/` instead. Each becomes a real Notion database
with typed properties, so you get board views, filters, and rollups. Then set
the NPC/Location/Session templates from `templates/` as Notion page templates
inside those databases.

Most people want both: databases for NPCs, Locations, Sessions and Quests;
plain pages for Lore and House Rules.

## Publish it on GitHub Pages

1. Create a repo and push these files to the default branch.
2. Edit `_config.yml`: set `title`, and if the site lives at
   `https://USER.github.io/REPO/`, set `baseurl: "/REPO"`. Leave `baseurl: ""`
   for a user or custom-domain site.
3. Update the `Edit on GitHub` link under `aux_links`.
4. Repo **Settings → Pages → Source: Deploy from a branch**, pick your branch
   and `/ (root)`.
5. Wait for the build (Actions tab shows it). First build takes a minute or two.

You get a sidebar, breadcrumbs, and client-side search from the
[just-the-docs](https://just-the-docs.github.io/just-the-docs/) theme, pulled in
remotely — nothing to vendor.

To preview locally:

```bash
bundle install
bundle exec jekyll serve
```

**Before you publish anything:** a GitHub Pages site is public, and so is a
public repo. Read `dm/README.md` first.

## Adding a page

1. Copy the matching file from `templates/` into the right folder.
2. Rename it `lowercase-with-hyphens.md`.
3. Fix the frontmatter — set `title` and change `parent: Templates` to the
   section name (`Characters`, `Locations`, and so on).
4. Delete the prompts as you fill them in.

Link between pages with relative Markdown links ending in `.md`
(`[Greyfen](../locations/greyfen.md)`). These work when browsing the repo on
GitHub *and* on the built site, because GitHub Pages rewrites them.

## Notes

- Frontmatter fields beyond `title`, `nav_order` and `parent` (`status`,
  `faction`, `cr`, `rarity`…) do nothing by default. They are there so the same
  files map onto Notion properties, and so you can build filtered lists later.
- Example pages are marked *example page* in their first line. Delete them once
  your own content exists — including `characters/marrow-quillane.md`,
  `locations/greyfen.md`, `factions/the-ashen-compact.md`,
  `sessions/session-01.md`, `quests/find-wren-halle.md`,
  `bestiary/fen-hag.md`, `items/the-sallow-lantern.md`.
- Sessions sort by `nav_order`. For newest-first, use negative numbers
  (`nav_order: -7` for session 7).
- Statblocks from published books do not belong on a public site. Reference the
  page number and note your changes.
