# Installation Guide

Türkçe: [`KURULUM-KILAVUZU.md`](KURULUM-KILAVUZU.md)

Set this framework up from scratch. No step is assumed.

---

## What this is

A project management layer. It:

- **Protects** — blocks deletions, stops secrets from being written into
  code, prevents touching the wrong directory on a customer server
- **Remembers** — where you left off, which decision you made and why,
  which error you solved and how
- **Tracks** — projects, tasks, service dates, device inventory
- **Individualises** — generates a distinct visual identity per project
  and audits template-looking layouts
- **Measures** — "done" is bound to a gate check, not an opinion

It is built for a single developer, not for teams.

---

## Requirements

| Requirement | Why | Required |
|-------------|-----|----------|
| Python 3.9+ | every script is Python | **Yes** |
| Git | sync and backup | Yes |
| `cryptography` package | password vault | If you use the vault |
| Bash | gate tests | If you run the tests |

On Windows, installing Git also provides Bash.

### Check

```bash
python --version
git --version
python -c "import cryptography; print('installed')"
```

If the encryption package is missing:

```bash
python -m pip install cryptography
```

> **Note for macOS and some Linux setups:** the `python` command may not
> exist, only `python3`. The test suite resolves the interpreter itself,
> but type `python3` when you run commands by hand.

---

## Installation

### 1. Get the files

```bash
git clone https://github.com/enverkocak/framework
cd framework
```

### 2. Check your environment

```bash
python plugins/enver-framework/scripts/kurulum/sihirbaz.py kontrol
```

It reports what is missing. A missing item disables that feature; the
rest still installs.

### 3. Install

**Windows:**
```powershell
.\kurulum.ps1
```

**Linux / macOS:**
```bash
chmod +x kurulum.sh
./kurulum.sh
```

### 4. Enter your identity

The framework was written for someone else; enter your own details:

```bash
python plugins/enver-framework/scripts/kurulum/sihirbaz.py kur \
  --gelistirici "<your name>" \
  --site "<your site>" \
  --eposta "<your e-mail>" \
  --sirket "<your company>"
```

### 5. Enable the plugin

```bash
claude plugin marketplace add enverkocak/framework
claude plugin install enver-framework@enver-framework
```

Restart afterwards.

**If a command does not resolve, use the namespaced form.** On a clean
install the short name may not resolve in every environment; the long
form always works:

```
/enver-framework:panel      /enver-framework:proje-devral
```

This was measured on a fresh machine: the short name can return
`Unknown command`, while all 30 commands resolve in namespaced form.

#### Scope

| Scope | Where it applies | Command |
|-------|------------------|---------|
| `user` (default) | **all projects** | `claude plugin install enver-framework@enver-framework` |
| `project` | that repository, shared with the team | `... --scope project` |
| `local` | that repository, only you | `... --scope local` |

### 6. Verify

```bash
python plugins/enver-framework/scripts/saglik/saglik.py bak
```

You should see **"Framework sağlıklı"** (framework healthy).

---

## First steps

### See the commands

```
/index
```

30 commands, what each does and how it is used.

### Register this machine

If you work on more than one computer:

```bash
python plugins/enver-framework/scripts/senkron/makine.py tanit --ad "<machine name>"
```

### Set up the vault

```bash
python plugins/enver-framework/scripts/kasa/kasa.py kur --kaynak <your secrets folder>
```

It asks for a password — type it **in your own terminal**, at least 8
characters. Then archive the plaintext source:

```bash
python plugins/enver-framework/scripts/ortak/arsiv.py <your secrets folder> \
  "Vault plaintext source" "Vault encrypted."
```

### Take over an existing project

The framework is not only for new projects. In the directory of the
project you are taking over:

```
/proje-devral
```

It scans the code, reads it with five parallel agents, writes a report,
**asks for approval**, and only then generates framework files. Nothing
is written before approval, and existing files are never overwritten.

---

## Directory layout

```
framework/
├── plugins/enver-framework/
│   ├── commands/           slash commands
│   ├── skills/             skills
│   ├── agents/             sub-agents
│   ├── hooks/              protections (activated via hooks.json)
│   ├── scripts/            script layer
│   ├── references/         rules, maps, catalogues
│   └── diller/             interface strings (tr, en)
├── bilgi/                  static notes
├── sablonlar/              project templates
│
├── hafiza/                 persistent memory — committed, synced
├── gunluk/                 raw session log — machine-local
├── kasa/                   encrypted vault — never committed
├── _calisma/               temporary work — never committed
└── _arsiv/                 finished work with a note — never committed
```

**The root stays clean.** Temporary files cannot be written there; a
protection blocks it.

---

## Language

Turkish is the default. To switch:

```bash
python -c "
import sys; sys.path.insert(0, 'plugins/enver-framework/scripts/ortak')
import ayarlar; ayarlar.yaz({'dil': 'en'})
"
```

Available languages live in `plugins/enver-framework/diller/`. To add
one, copy `tr.json` and translate it. Files must carry the same keys —
the health check verifies this.

---

## After installation

### Full test

```bash
bash plugins/enver-framework/scripts/testler/tumunu-calistir.sh
```

12 phase gates, 127 scenarios, health and security verifications.
About 40 seconds. Everything must pass.

### Troubleshooting

**"Protections are not running"** — run the health check. If it says
protections come from the plugin, that is the normal path since 3.0.0;
`settings.json` registration is only used in a development clone.

**A command is not recognised** — use the namespaced form:
`/enver-framework:<command>`.

**Turkish characters look wrong in the terminal** — the files are UTF-8;
the terminal's code page is the usual cause, not the file.

---

**Developer:** Enver KOCAK · enverkocak.com · mail@enverkocak.com
