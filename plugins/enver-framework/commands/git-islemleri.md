---
description: Git islemleri - branch, commit, PR, merge, conflict cozme
argument-hint: Opsiyonel - bos birak = menu, veya direkt (status, branch, pr, merge)
---

# Git Islemleri

Git ve GitHub islemlerini interaktif olarak yonet.

## MENU (arguman yoksa AskUserQuestion ile goster)

```
[1] Durum               git status + son commitler
[2] Branch Olustur      Yeni branch ac (feature/fix/hotfix)
[3] Branch Degistir     Branch listele ve sec
[4] Commit              Degisiklikleri commit et
[5] PR Olustur          GitHub PR olustur
[6] PR Listele          Acik PR'lari listele
[7] Merge               Branch birlestir
[8] Cakisma Coz         Merge conflict coz
[0] ← Ana Menu
```

## NASIL CALISIR

### [1] Durum
`git status`, `git log --oneline -10`, `git diff --stat`

### [2] Branch Olustur
Kullaniciya sor:
- Tip: feature / fix / hotfix
- Isim: kisa aciklama (turkce, tire ile)
→ `git checkout -b [tip]/[isim]`

### [4] Commit
1. `git diff --stat` goster
2. Degisiklikleri analiz et, commit mesaji oner
3. Kullanici onaylar veya degistirir
4. `git add [dosyalar]` + `git commit`

### [5] PR Olustur
1. Branch bilgisini goster
2. Baslik ve aciklama olustur (commit'lerden)
3. Kullanici onaylar
4. `gh pr create --title "..." --body "..."`

## KURALLAR
- Force push ASLA yapilmaz (kullanici acikca istemezse)
- --no-verify KULLANILMAZ
- Main/master'a direkt push YAPILMAZ, uyari ver
