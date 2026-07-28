# Changelog

Türkçe: [`DEGISIKLIKLER.md`](DEGISIKLIKLER.md)

Version history of Enver Framework.

Recording style: every release states **what changed** and **why**.
Without the "what" the history is meaningless; without the "why" it
teaches nothing.

---

## 3.3.5 — The update notice could not see the installed copy

`/guncelle` was run and the truth came out: the repository had been at
3.3.4 for days while the **running plugin was still 3.2.9**. The command
never said so — it said "up to date". Two bugs were stacked on top of
each other.

**1. Reading the version assumed a directory layout.** `yerel_surum()`
looked for the manifest at `parents[2]`:

| Layout | Script | Manifest |
|--------|--------|----------|
| Repository clone | `plugins/enver-framework/scripts/` | `parents[2]` **correct** |
| From a marketplace | `cache/<plugin>/<version>/scripts/` | one level deeper, **not found** |

On every marketplace install the version read as `None`. The failure was
silent: the comparison became meaningless, `var_mi` could never be true,
and so **an installed copy could fall months behind without a word**. The
depth is no longer assumed; the first manifest upwards is used.

**2. The update never touched the running copy.** `git pull` plus the
installer write into `~/.claude/plugins/`. But on a marketplace install
the live copy is the cache, not that folder. The command reported
success while the user stayed on the old version — exactly what happened.

Worse, running both paths left a **second, parallel installation** in
`~/.claude/plugins/`: the same commands and hooks in two copies, with no
way to tell which is live. And the clone may be the **private
development repository** rather than the public one — in which case the
installer would spread a copy that was never meant to be shared.

`/guncelle` now picks the source first: on a marketplace install it runs
`claude plugin marketplace update` + `claude plugin update` and leaves
the clone alone; on a clone install the old path applies.

**Third**, the session banner gained a line: when the installed copy
falls behind the running code it says so. That gap was previously
invisible everywhere.

**Measured:** update scenarios went from 7 to **17**. Version reading is
measured against real directory trees in both layouts (one marketplace,
one repository), the stale-installed-copy case with three scenarios, and
the choice of update path with two.

**Full suite: 632 passed, 0 failed.**

## 3.3.4 — The installer no longer touches the vault at all

The question was whether updating breaks the vault. It was measured: it
did not. But the reason was an accident, not a protection — the source
has no `vault/` folder, so the copy step happened to do nothing. **If
that folder ever came back, the user's encrypted vault would be
overwritten with `-Force`**, and nothing measured it.

The rule is explicit: vault files are never committed, logged, printed or
**copied**. The installer had been left outside that rule.

**What changed:** both installers stopped copying the vault entirely. The
folder is created if missing and its contents are left alone. If the
source does contain a vault folder it is not carried over — you are told
`KOPYALANMADI (kural geregi)`, "not copied, by rule". A vault is created
by `kasa.py kur` and belongs to that machine.

**Measured:** `kurulum-testleri.py` went from 24 to **32 scenarios**. The
worst case is built: a vault in the source *and* in the target, with the
**same file name** — where a copying installer really would destroy it.
The installed vault is checked to be **byte for byte** unchanged.

The scenarios were themselves tested: the copy line was deliberately put
back, and seven checks failed across both operating systems. They failed
again when the line was written differently — the test does not look for
one specific line, it measures that **no copying line mentions the
vault**.

**Documentation:** both installation guides now say where the vault lives
and what carries it away: `git pull` is safe (the vault is untracked),
but updating by cloning into a fresh folder leaves it behind, and
`git clean -xfd` deletes it. Vaults do not sync.

### A second finding from the same run: the generated copy was mistaken for a project

The full suite went red in two places at once, both with the same root:
the mirror folder produced for sharing was being counted as an
**independent project**.

- It showed up in the registry as an "undefined project" and the phase 4
  gate failed.
- Worse: parts of the folder name became personal-data patterns. With
  `...-framework-acik` registered, **`framework`** became a searched word,
  matched in 96 files, and the clean copy was declared **unshareable** —
  the release pipeline was locked with no real leak anywhere.

Two fixes: (1) `paylasima-hazirla` leaves a `.enver-ayna` marker in the
target, and the scan does not count a folder carrying it as a project —
the record is not deleted, only hidden from the listing. The marker holds
no path and no identity, because that file sits in the shared folder.
(2) `framework`, `cerceve`, `kaynak`, `surum` and `yedek` joined the
common-word list: a generic technical word is not personal data.

Phase 10 gained three checks. One of them measures the opposite
direction: the same folder **without** the marker must still count as a
project — otherwise the check would pass vacuously by calling nothing a
project.

**Full suite: 622 passed, 0 failed.**

## 3.3.3 — The upgrade path never worked on Mac and Linux

Someone asked how a user on the first version reaches the latest one.
Writing the answer showed the path itself was broken — and had been since
day one.

| Where | What happened |
|-------|---------------|
| `kurulum.sh` | The vault and knowledge folders were copied **unconditionally**. The public release has neither; `cp` failed, `set -e` stopped the installer on the spot, and it exited **without ever copying the plugin**. |
| `guncelle.sh` | It said `git pull origin master`. The public repository lives on `main`, so no update ever arrived. |
| `kurulum.ps1` | An installed `CLAUDE.md` was overwritten with no backup. Rules the user had written into it could not be recovered. |

The first one hit not only fresh installs but **every update**:
`/guncelle` runs `kurulum.sh` as its second step, so one-command updating
died at the same line. Windows already skipped missing sources — the same
script behaved differently on the two systems.

**Fixes:**

- `kurulum.sh` skips a missing source instead of stopping. Same behaviour
  as Windows.
- `guncelle.sh` names no branch; it pulls the tracked one (`--ff-only`),
  and no longer keeps its own copy list — it calls `kurulum.sh`. Two
  lists drifting apart meant an update could reinstate bugs the installer
  had fixed.
- The rules file is backed up before being overwritten:
  `~/.claude/enver/yedek/CLAUDE.<date>-<time>.md`, and only when the
  content actually differs.
- The comparison uses .NET instead of `Get-FileHash`: on a locked-down
  machine that cmdlet was not found and the installer stopped exactly at
  the backup step — caught live while writing the scenarios.

**Documentation:** both installation guides gained an "upgrading from an
older version" section. The point that had to be written down: `/guncelle`
**only exists from 2.13.0**. Older installs have neither the command nor
`~/.claude/enver/kurulum-bilgisi.json`, which records where the clone
lives, so the command cannot find the repository. The first hop is
manual; everything after it is one command.

**Measured:** `kurulum-testleri.py` — 24 scenarios. The installer really
runs, but inside a sandbox: `HOME` (and `USERPROFILE` on Windows) points
at a temporary directory, so the real `~/.claude` is never touched. The
source tree is built without the vault and knowledge folders — the state
of the public release — and the plugin is verified to arrive. Wired into
the suite.

## 3.3.2 — Bilingual coverage went beyond the command documents

"Let everything have English" was measured: all 30 command documents were
bilingual, but **15 documents were still single-language** and no check
measured it.

| Where | Files |
|-------|-------|
| Agents | 5 |
| Skills | 4 |
| Templates | 4 |
| Rules reference (`references/kurallar.md`) | 1 |
| Example rules (`CLAUDE.ornek.md`) | 1 |

Each gained an English section. The agent and skill sections describe not
what they do but **how they behave**: the takeover agent "reports what it
found, never what it assumes"; the security agent "never prints secret
values, only the file and line"; the discovery skill "no coding before
discovery finishes".

**The vault section was completed.** The guide covered daily use but not:
how the first-time setup works, that the plaintext source must be
archived, that the vault is **per-machine** (`kasa/` never syncs, set it up
on each computer), and what happens if the password is lost. The English
section was also missing the `liste` and `yaz` commands and the warnings.

**Bound to the gate.** Phase 10 now looks for an English section in agents,
skills, templates and the rules reference too. Add a single-language agent
or skill and the suite fails.

Full suite: **587 passed, 0 failed** (exit code 0).

## 3.3.1 — The vault check printed but did not measure

The regression check added in 3.3.0 **printed** the vault size without
comparing anything; it passed unconditionally. If the vault were clobbered
again, the suite would still say "passed".

A check that does not measure is not a check — three examples surfaced
today (the runner not counting a failed section, the panel miscounting its
own menu, and this one).

The vault section now records the file's size and timestamp at the start
and compares them at the end. Vault content is never read; only metadata
is inspected.

**Verified against the real vault:** the user's vault was restored from
the archived source (3 files, 1846 bytes), the test password no longer
opens it, and the file was byte-identical after a full suite run.

Full suite: **586 passed, 0 failed** (exit code 0).

## 3.3.0 — A gate test was destroying the user's password vault

The most serious finding of the day. The vault was created on 21 July, a
password was set, and the plaintext source was archived. Yet **every full
suite run deleted the real vault and wrote a test vault in its place.**

While exercising the vault engine, `faz2-kapi.sh` called:

```
kasa.py kur --kaynak _calisma/kasa-testi --parola "KapiTesti2026!" --uzerine-yaz
```

The vault path resolves through `proje_kok()`, the test had never been
wired to the sandbox, and the overwrite flag replaced the file without
asking. The result: the user could no longer open the vault with their own
password, because the file now held the test's 13-character content and
the test's password.

**How it surfaced:** the question "what are we setting the vault up for?"
was asked. Measuring the state showed the vault was already installed —
but the file was 162 bytes and had changed today. It opened with the test
password: `a.md` was all it contained.

**No data was lost.** The plaintext source had been archived on 21 July;
the "nothing is ever deleted" rule genuinely paid off here.

**Fix:** the vault tests run in the sandbox (the same redirection applied
to memory in 3.1.2), plus a regression check measuring that the real vault
file is untouched during the run.

This is the gravest instance of the same class as the memory pollution.
There, a test writing to real state produced noise; here it took away the
user's passwords.

Full suite: **586 passed, 0 failed** (exit code 0).

## 3.2.9 — The whole repository page is bilingual

The previous two releases made the headings and two tables bilingual, but
the **body text** was still single-language: the sentences under "Why it
exists", the explanations around the install steps, the customise section,
the test and contributing paragraphs were Turkish only. A non-Turkish
reader understood the heading and not the sentence beneath it.

The README was rewritten: **every Turkish paragraph is followed by its
English counterpart**, every table carries both languages, and every link
has its English equivalent next to it.

- The "Why it exists" and "Customize" tables are bilingual in place (one
  table, two languages per cell).
- The flow-chart node labels are written in both languages.
- Single-language links such as "full list" gained an English counterpart.
- Two notes were added to the install section: the namespaced command form
  when a short name does not resolve, and `python3` instead of `python` on
  macOS.
- Stale information was corrected: hooks are activated through the
  plugin's `hooks.json`, not `.claude/settings.json` (true since 3.0.0).

Full suite: **585 passed, 0 failed** (exit code 0).

## 3.2.8 — The "what it does" columns are bilingual too, and counts are measured

Headings became bilingual in 3.2.7, but the **contents** of the tables
were still single-language: the "Ne yapar" column of the command and
protection tables was Turkish only. A non-Turkish reader understood the
heading but not the rows.

- A **"What it does" column** was added to both tables, so every row reads
  in either language.
- Missing rows were filled in: `/proje-devral` (the headline feature of
  3.1.0) was absent from the command table, and `iz-kontrol.py` from the
  protection table.

**The component counts were wrong.** The README said "29 commands, 3
skills, 4 agents, 48 scripts"; reality is **30 commands, 4 skills, 5
agents, 53 scripts**. That is the third count to drift today (27 commands,
then 105 scenarios, now this).

Hand-written numbers go stale, so this is now **bound to the gate**: Phase
10 counts the directories and compares them with the README. Add a
component without updating the README and the suite fails.

Full suite: **585 passed, 0 failed** (exit code 0).

## 3.2.7 — The repository page can be scanned in both languages

3.2.5 added an English summary block, but the body of the page was still
single-language: **Neden var, Kurulum, Kilavuzlar, Icinde ne var,
Korumalar, Nasil calisir, Uyarlama, Test, Katki, Lisans** were all Turkish
headings. Past the summary block, a non-Turkish reader hit a wall again.

The content already existed - `README.en.md` is a full mirror. What was
missing was **signposting**.

- Headings in both READMEs are now bilingual: `## Neden var - Why it
  exists`, `## Kurulum - Install`, and so on. The page can be scanned in
  either language, and the reader can jump to the English document from
  the section they were looking for.
- The guides table has two columns: Turkish and English side by side.
  Previously only the Turkish rows were listed, so the English documents
  were invisible from the page.
- The repository description (About) is written in English, so search
  results and the page title now start in English.

Why it matters: open-source work is not evaluated unless it is read. If
the page offers no handle in the reader's language, complete content
reaches nobody.

Full suite: **584 passed, 0 failed** (exit code 0).

## 3.2.6 — The path audit caught an error in my own document

The English block added in 3.2.5 pointed at `diller/en.json`; the real
path is `plugins/enver-framework/diller/en.json`. A newcomer would have
been sent to a file that does not exist.

The path audit caught it — but the release went out anyway: the suite
printed "FAILED" while its exit code was masked by a pipeline. The lesson
concerns the gate itself: a gate is only a gate if its exit code is read.

The path was fixed and the full suite verified together with its exit
code.

Full suite: **584 passed, 0 failed** (exit code 0).

## 3.2.5 — The repository page introduces itself to non-Turkish readers

The repository is public and MIT licensed, yet **not one line of English
appeared above the fold** on github.com. A language switch existed
(`Türkçe · English`) but it was a small link; someone seeing Turkish
headings would close the page before noticing it.

An **English summary block** now sits at the top of the README, right
under the badges: what this is, what it does, the licence, and direct
links to the four English documents. It also states plainly that the
interface defaults to Turkish while the language layer ships with English
— so nobody installs it and is surprised.

Why it matters: open-source work is not evaluated unless it is read. A
page that does not answer "is this useful to me" in the first ten seconds
gets closed.

Full suite: **584 passed, 0 failed.**

## 3.2.4 — The suite said "all passed" while a section had failed

Testing the update banner end to end on the second computer surfaced
three bugs at once, all from one root: **the measurement was not measuring
what it believed it measured.**

### 1. This time the banner never appeared

3.2.2 closed the false warning; the opposite direction opened. Once the
cached remote version went stale, a new release was **never** announced
for a day.

Fix: if the local version changed since the cache was written (that is, an
update happened), the cached remote value may be stale too - the cache is
skipped and the network is polled once. With no network, the stored
verdict is no longer returned as-is; the remote version is compared
against the live local one.

### 2. A scenario suite ran but was NOT COUNTED

The runner looked for the result line in fully Turkish spelling only. The
trace scenarios were rewritten in 3.2.0 with ASCII output, so from that
day **24 scenarios ran without entering the total**.

I noticed the drop earlier and explained it as "scenarios merging" - that
was wrong. This was the cause.

### 3. A failed section did not fail the run

Worse: when the result line could not be read, the section printed
`[KALDI]` but was never added to the failure total. Two "FAILED" lines
were on screen while the summary said **"ALL PASSED, 0 failed"**.

A gate that says "passed" while knowing it is shut is not a gate. Now: an
unreadable suite counts as broken, a non-zero exit code counts as a
failure, and both spellings are read.

### New suite: guncelleme-testleri.py (7 scenarios)

The banner can err in both directions and both mislead the user: a false
warning ("I updated but it still says so") and silence ("a new version
exists but nothing is said"). Seven scenarios measure both; no network
required.

Full suite: **584 passed, 0 failed** (the previous count of 553 was
incomplete).

## 3.2.3 — The panel miscounted its own menu

`/panel` described itself as "4 tabs, 16 categories, **80+ operations**".
The menu was counted: tabs and categories were right, the operation count
was not — there are **58**, not 80+.

A small gap, but the same class of defect: the document walked one step
ahead of reality. The numbers are now measured from the menu itself.

**Note:** the 30 slash commands and the panel's 58 operations are
different things. "How many commands are there" is 30; "how many
operations can I run" is larger, because the panel is a menu layer of its
own.

Full suite: **553 passed, 0 failed.**

## 3.2.2 — The update banner did not clear after updating

The update flow was tested end to end on the second computer. The banner
appeared correctly, `/guncelle` ran, the clone reached 3.2.1 — and the
startup briefing still said **"UPDATE AVAILABLE: 3.2.0 → 3.2.1"**.

**Cause:** update status polls the network once a day and reads from a
cache in between. The cache remembered not only the remote version but
the **local** one too. After updating, the local version changes while
the cache keeps repeating the old one for a day.

`guncelleme.py yap` cleared the cache, but the shell scripts
(`guncelle.ps1` / `guncelle.sh`) did not — so anyone updating that way saw
a false banner for a day and concluded the update had failed.

**Fix:** the local version is never cached; it is read from the file every
time. The network is needed for the remote version only; the local one can
be measured instantly. **What can be measured is not read from a cache** —
the shared lesson of the seventh bug fixed today.

A regression check was added: if the banner logic stops measuring the
local version live, the suite fails.

Full suite: **553 passed, 0 failed.**

## 3.2.1 — Everything in both languages

The framework lives in a public repository, but most documents existed
only in Turkish: only the README had an English counterpart. A newcomer
who read the installation steps hit a Turkish wall at the guide.

**Added:**

| Document | Contents |
|----------|----------|
| `KURULUM-KILAVUZU.en.md` | the complete installation guide |
| `KULLANIM-KILAVUZU.en.md` | the complete user guide |
| `DEGISIKLIKLER.en.md` | version history from 3.0.0 onward |

Turkish documents link to their English versions and vice versa.

**All 30 command documents gained an English section** describing what
the command does and how it is invoked, including the namespaced form.

**Bound to the gate (11 new checks).** Being bilingual is now a
measurement, not an intention: do all four documents exist in both
languages, are the cross-links in place, do all 30 commands carry an
English section, do `tr.json` and `en.json` share the same keys. If
anything falls back to one language, the Phase 10 gate closes.

**Release notes are published in both languages** from now on; until
today they were Turkish only.

Full suite: **552 passed, 0 failed.**

## 3.2.0 — The trace rule narrowed to code comments

**The rule changed.** The ban on tool traces now covers **code comment
lines only**. Documentation, prose, string values, commands and paths are
free.

**Why:** the old rule scanned entire files and interrupted work
constantly. An installation command, a file path, a sentence in a
document — even a test's own fixture data — produced warnings. It fired
falsely four times in a single session. An audit that cries wolf stops
being read, and then misses the very line it exists to catch.

What remains is clear and defensible: **shipped source code carries no
generator trace in its comments.** A comment is the voice of whoever
wrote the code; no other name belongs there.

- `iz-kontrol.py` now scans comment by comment. Comment syntax is defined
  for 30+ extensions: `#`, `//`, `/* */`, `<!-- -->`, `--`, `<# #>`.
  Block comments are tracked across lines.
- Exemption logic was kept: if a comment documents an installation
  command or a file path, that is not a trace. If the same comment holds
  both a path and a generator phrase, it still warns.
- It is a simple scanner; it does not distinguish a `//` inside a string.
  When it errs it errs by catching **more**, not less — the safe side for
  a trace audit.
- `devral.py` uses the same extractor from the hook, so the takeover scan
  and the audit share one definition and cannot drift apart.
- Scenarios rewritten: 18 → **24**.
- Commit authorship is a separate rule and unchanged: the author is
  Enver KOCAK; no co-author line is added.

**Measured on a second machine:** the framework was installed from
scratch on another computer and **all 30 commands resolved**. The short
name does not work there (`/panel` → `Unknown command`) while
`/enver-framework:panel` does. Same version, same plugin, same settings;
the cause of the difference was not found. The guides now document the
namespaced form — measured reality, not a guess.

Full suite: **540 passed, 0 failed.** 127 scenarios.

## 3.1.7 — The health check called a clean install sick

The framework was installed on a second computer for the first time.
Installation was clean and the gate tests passed 160/0 — but the health
check reported **2 BROKEN**, both false alarms.

**"No settings file — no protection may be running."** The audit looked
for protections in `.claude/settings.json`. Since 3.0.0 hooks arrive
through the plugin's `hooks.json`; the installer deliberately registers
nothing. So **every ordinary user** saw this warning — in the very tool
whose job is to answer "is the framework actually working". That is the
worst kind of false alarm: it makes a correctly installed system look
broken. The audit now recognises both valid paths, and asks the copy that
actually runs.

**"The raw log is being committed."** `git check-ignore -q gunluk` was
called. If the folder does not exist yet, git does not treat `gunluk` as
a directory, the `/gunluk/` pattern does not match, and a fresh install
**always** reported a false break. A trailing slash was added.

## 3.1.6 — Gate tests stopped depending on one machine

The engine itself had no hardcoded paths; the tests did.

- 241 `python` calls were bound to a resolved interpreter. On macOS that
  command often does not exist, only `python3`. Existence is not enough —
  the candidate must **run**: on Windows a Microsoft Store shortcut named
  `python3` is found but fails. The first version of this fix dropped 285
  checks for exactly that reason; the suite caught its own fix.
- Phase 0's customer-project fixture moved to the system temp directory.
- Phase 4's scan-root test now measures the **rule** (roots are defined,
  exist, are not the filesystem root, and hold all projects) instead of a
  specific drive path.
- CI matrix gained `macos-latest`. A portability claim is only true if it
  is measured.

## 3.1.5 — Cleaning that did not reach the source did not last

In 3.1.2 memory was cleaned of test residue. Here the first session
summary brought it **back** — the leak gate caught it.

- The session summary is produced from `gunluk/komutlar.jsonl`; the 104
  test records there returned to memory on the first summary. The cleaner
  and the leak audit now cover the raw log too. A file that never enters
  the repository but produces one that does cannot stay outside the audit.
- The raw log was never rotated: `oturum.py bitir` archived it only with
  an explicit flag, which nobody passed. Every summary therefore
  re-summarised all history. Rotation is now the default (archived, never
  deleted); `--gunlugu-birak` opts out.

## 3.1.4 — The status line counts tokens; the audit stopped calling paths traces

An integrity audit found no broken links, but three behaviour bugs:

- **A file path was counted as a trace.** Every script writing an
  absolute path carries the repository name. Exemption now requires a
  slash, so prose cannot slip in.
- **The status line shows tokens instead of cost.** The figure is *newly
  processed* tokens: input + cache writes + output. Cache reads are
  deliberately excluded — measured, 74.5M of cache reads corresponded to
  1.4M of real consumption. A counter reading "76M" would be misleading,
  not accurate. Context fill is shown separately. Counting is incremental.
- **The phase indicator had silently gone blank.** It read a heading from
  a document removed in 3.1.2. The phase plan lives in the engine's own
  record, and that is what it reads now.

## 3.1.3 — The dry run was asking dead hooks

A dead copy of `hooks/` from 3.0.0 sat in the repository root. Nobody
read it, and it had silently drifted: its `iz-kontrol.py` never received
the 3.1.1 fix.

The real bug appeared where that copy was used: `kuru-deneme.py` (the dry
run) looked for hooks in **two places, both the repository root**. So its
promise — "does not guess, asks the real protections, report and reality
cannot diverge" — had not held for months.

A wrong-answering security tool is worse than none: you trust a report
that says "no obstacle" and run the command. Removing a copy is a sturdier
fix than trying to keep two in sync.

## 3.1.2 — Gate tests stopped writing to real memory

The framework's own memory had filled with its own tests' rubbish. The
startup briefing answered "where did we leave off" with thirty test
lines.

| File | Total | Test residue |
|------|-------|--------------|
| `hafiza/gorevler.json` | 393 records | **390** |
| `hafiza/cihaz-envanteri.json` | 124 devices | **124** (all) |
| `hafiza/durum.md` | 1513 lines | **772** |

- **Sandbox** (`testler/_kumhavuzu.sh`): writing checks are called with
  `CLAUDE_PROJECT_DIR` so records land in the working area. Only *writing*
  checks were redirected; readers still see the real repository, otherwise
  the test would not measure what it exists to measure.
- **`sizinti-kontrol.py`** measures that the fix stays fixed. It looks for
  the tests' record signatures, not for the phrase itself — a real session
  summary may legitimately mention gate tests.
- **`artik-temizle.py`** removed the accumulated residue. Nothing was
  deleted: the whole of memory was copied to the archive first.

## 3.1.1 — The trace audit learned context

`iz-kontrol.py` searched whole files for the tool name. But the framework
is a plugin: installation documents must contain the install command,
settings paths must contain the settings directory. The audit fired at
all of them.

Scanning became line-based, and exempt machine forms (paths, environment
variables, commands, package names, addresses) are stripped **before** the
search. A product name in prose remained a violation — that was the point
of the rule.

Six documents also described files the engine never reads; those paths
were corrected to the engine's real sources.

## 3.1.0 — Existing projects can be taken over

Until now the framework assumed a project started from zero. But most
work enters **code that already exists** — an old customer site, a
repository untouched for a long time. `/proje-devral` closes that gap: it
reads the project, writes down what it learned, **asks for approval**, and
only then wires the project into the framework.

## 3.0.0 — A standard plugin

The framework became a proper Claude Code plugin. Hooks moved inside the
plugin (`hooks.json`), the root marketplace manifest enables installation
straight from the repository, and the installer no longer registers hooks
separately — a single delivery path, with no double execution.

---

Older entries are kept in Turkish in [`DEGISIKLIKLER.md`](DEGISIKLIKLER.md).
