# User Guide

Türkçe: [`KULLANIM-KILAVUZU.md`](KULLANIM-KILAVUZU.md)

Daily use of the framework: which command to run when, and why each rule
exists.

**Developer:** Enver KOCAK · enverkocak.com · mail@enverkocak.com

---

## Daily flow

### When a session opens

Nothing to do. The startup hook brings you:

- which machine you are on
- whether the last session ran on a different machine (local data may be stale)
- **where you left off** — the previous session summary
- recent decisions and recently solved errors

If it does not appear:
`python plugins/enver-framework/scripts/hafiza/oturum.py brifing`

### While working

The system records in the background: which command you ran, which file
you changed. **Passwords are masked before they reach the log.**

When you make a decision or solve an error, record it immediately:

```bash
H="plugins/enver-framework/scripts/hafiza"

python "$H/defter.py" karar ekle "<title>" "<reasoning>"
python "$H/defter.py" hata ekle "<symptom>" "<solution>" --nerede "<context>"
```

Before starting on an error, search first — it may already be solved:

```bash
python "$H/defter.py" hata ara "<symptom>"
```

### When the session ends

```bash
python "$H/oturum.py" bitir --not "<handover note>" --sirada "<next task>"
python plugins/enver-framework/scripts/senkron/senkron.py gonder
```

The raw log is rotated (archived, never deleted) after the summary, so
each summary covers one session rather than repeating all history.

---

## Starting a new project

**Do not jump into code.** The order is:

### 1. Discovery (four stages, cannot be skipped)

```bash
K="plugins/enver-framework/scripts/plan/kesif.py"

python "$K" baslat --proje "<name>" --musteri "<customer>"
python "$K" sorular
python "$K" yaz "<finding>"
python "$K" ilerle
```

| Stage | What happens |
|-------|--------------|
| 1. Requirements | Ask the customer, write answers **in their words** |
| 2. Research | What else might be needed, what is being forgotten |
| 3. Clarification | Ask what research surfaced; leave no ambiguity |
| 4. Plan | Split into phases, give every phase a gate check |

Until discovery finishes, the tool says **"do not start coding"**.

> **Small jobs:** four stages are overkill for a one-file fix. The test:
> if it takes more than a day or ships to a customer, run discovery.

### 2. Project definition

```bash
P="plugins/enver-framework/scripts/projeler"

python "$P/proje.py" olustur --ad "<name>" --gorev "<what it does>" --musteri "<who>"
python "$P/tani.py" bu
python "$P/proje.py" dogrula
```

**No password goes into the definition.** Secrets live in the vault; the
`kasa_anahtari` field only points at the vault record.

---

## Taking over an existing project

The order above is for greenfield work. In an inherited project — an old
customer site, a repository untouched for months, someone else's code —
you learn by **reading the code**, not by asking questions.

```
/proje-devral
```

| Step | Work |
|------|------|
| 1 | Mechanical scan — directory map, entry points, dependencies, history, unfinished work, committed secrets, identity-rule violations |
| 2 | Five agents read in parallel: architecture, data, process, rules, unfinished work |
| 3 | Findings are merged; conflicting findings are written down, not hidden |
| 4 | The plan is shown and **approval is requested** |
| 5 | Only after approval are framework files generated |

### Unbreakable rules

1. **No file is written without approval.** Scan and plan touch nothing;
   they only leave a report under `_calisma/devralma/`.
2. **Existing files are never overwritten.**
3. **Secret values are never printed** — only `file:line` and the type,
   otherwise the report itself becomes the leak.
4. **Critical risks are repeated at the end**, never passed over quietly.

---

## Command reference

All commands: `/index`

**If a command does not resolve, add the namespace.** On a machine where
the framework is installed as a plugin, the short name may not resolve in
every environment; the long form always works:

```
/enver-framework:panel      /enver-framework:proje-devral
```

| Group | Commands |
|-------|----------|
| Daily | `/index` `/panel` `/hafiza` `/ara` `/durum-kaydet` |
| Project | `/kesif` `/projeler` `/sema` `/proje-baslat` `/proje-devral` `/faz` |
| Design | `/tasarim` |
| Security & upkeep | `/kasa` `/saglik` `/senkron` `/guvenlik-tara` `/guncelle` `/faz-kontrol` `/temizlik` `/framework-ayarlari` |
| Framework upkeep | `/surum` `/dokumantasyon` `/toplu-islemler` |
| Server & ops | `/monitoring` `/log-izle` `/db-yonetimi` `/backup` `/git-islemleri` `/canli-kontrol` `/web-kontrol` |

---

## Protections

Hooks run **before** a command executes, through the plugin's
`hooks.json`.

| Hook | What it does |
|------|--------------|
| `veri-koruma.py` | Blocks deletions; asks before destructive commands |
| `kasa-koruma.py` | Blocks direct vault access and secrets written into code |
| `sunucu-koruma.py` | Blocks access outside the permitted directory on a customer server |
| `git-gizlilik-koruma.py` | Blocks making a repository public |
| `iz-kontrol.py` | Scans **code comments** for tool traces |
| `yazim-kontrol.py` | Checks the Turkish character rule |
| `oturum-kayit.py` | Records work silently; masks passwords |
| `oturum-acilis.py` | Gives the "where did we leave off" briefing |
| `tam-yetki.py` | In full-authority mode, permits routine work; stays silent on exceptions |
| `kalite-kapisi.py` | Binds saying "done" to the gate check |

### Why deletion is blocked

Nothing is deleted; finished work is archived with a note. Archiving is
safer than deleting: the record survives and can be restored.

### The trace rule (narrowed in 3.2.0)

Tool names are forbidden **in code comment lines only**. Documentation,
prose, string values, commands and paths are free.

The earlier rule scanned entire files and interrupted work constantly — an
installation command, a file path or a sentence in a document triggered
warnings. An audit that cries wolf stops being read, and then misses the
line it exists to catch.

---

## Vault

```bash
K="plugins/enver-framework/scripts/kasa/kasa.py"

python "$K" durum       # locked or open, how long is left
python "$K" ac          # unlock (asks for the password)
python "$K" liste       # list the records
python "$K" oku <file>  # read one record
python "$K" yaz <file>  # add or update a record
python "$K" kilitle     # lock
```

**Important:**
- Type the password **in your own terminal**; never into the conversation
- Decrypted content is **never written to disk**
- The vault locks itself when the time is up (60 minutes by default)
- Do not try to read the vault file directly — a protection blocks it, and
  it is encrypted anyway

### First-time setup

The vault is built from a plaintext folder:

```bash
python "$K" kur --kaynak <your secrets folder>
```

It asks for a password (at least 8 characters). Afterwards **archive the
plaintext source** instead of leaving it in the project — if the same
secrets sit in two places, the encrypted one protects nothing:

```bash
python plugins/enver-framework/scripts/ortak/arsiv.py <your secrets folder> \
  "Vault plaintext source" "Vault encrypted."
```

### The vault is per-machine

`kasa/` is kept out of the repository (never committed), so it **does not
sync**. Set it up separately on each computer. Memory travels between
machines; secrets do not — that separation is deliberate.

### If you forget the password

There is no recovery; the vault will not open. The way back is to rebuild
it from a source folder:

```bash
python "$K" kur --kaynak <source folder> --uzerine-yaz
```

`--uzerine-yaz` **replaces** the existing vault. If it holds records you
cannot reach, try to recover those first.

---

## Memory and multiple computers

| Area | Contents | Committed |
|------|----------|-----------|
| `hafiza/` | summarised, lasting knowledge | **Yes** — syncs between machines |
| `gunluk/` | raw session log | No — stays on the machine that produced it |

```bash
S="plugins/enver-framework/scripts/senkron"

python "$S/senkron.py" durum
python "$S/senkron.py" cek      # before starting work
python "$S/senkron.py" gonder   # after finishing
```

**Conflict protection:** if the remote has newer records, sending stops
instead of overwriting. If local changes are unprocessed, pulling stops.
Two machines cannot erase each other's work.

---

## Phase engine and full authority

```bash
F="plugins/enver-framework/scripts/faz/faz.py"

python "$F" durum
python "$F" ilerle     # runs the gate; passes only if it passes
```

**"Done" is a measurement, not an opinion.** A gate is a command; the
gate opens only when the exit code and the remaining-count are zero.

### Working modes

`dikkatli` (default) · `hizli` · `sunucuda` · `tam-yetki`

In full-authority mode permission is not requested until the phase ends —
but **no protection is disabled**. Even in that mode these still stop:
vault, deletion, remote server, going live, repository visibility,
irreversible database operations, payment.

---

## Troubleshooting

### Full test

```bash
bash plugins/enver-framework/scripts/testler/tumunu-calistir.sh
```

12 phase gates, 127 scenarios, health check, functional and security
verifications. About 40 seconds.

### A protection blocks something wrongly

The block message states **why** it was blocked and **how** to fix it. If
it really is wrong, correct the pattern in that hook, then run the
protection scenarios.

### See what would happen before running a command

```bash
python plugins/enver-framework/scripts/kuru-deneme.py "<command>"
```

It does not guess: it asks the real protections and reports their
decision.

### Restore from a backup

Nothing is deleted, so restoring means copying back from `_arsiv/`. Each
archive folder carries a `NEDEN.md` explaining why it was archived.
