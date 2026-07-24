---
description: Nerede kaldigini kaydeder, sonraki konusmaya hazirlar
argument-hint: Opsiyonel - ozel not eklemek icin
---

# Durum Kaydet

Mevcut calisma durumunu kaydet ki sonraki konusmada kaldigi yerden devam
edilebilsin.

## Nerede tutulur

Durum kaydi **`hafiza/durum.md`** dosyasindadir. Acilis brifingi (SessionStart
kancasi) o dosyayi okur; baska bir yere yazilan kayit bir sonraki oturumda
gorunmez. Dosyayi elle yazma, oturum katmanini kullan.

| Dosya | Ne tutar |
|-------|----------|
| `hafiza/durum.md` | Son durum - nerede kaldik |
| `hafiza/oturumlar/<tarih>-<no>.md` | O oturumun tam ozeti |
| `hafiza/kararlar.md` | Verilen kararlar, gerekcesiyle |
| `hafiza/hatalar.md` | Cozulen hatalar, cozumuyle |

## 1. Bilgi Topla

- **Git durumu:** `git status` ve `git log --oneline -10`
- **Faz durumu:** `python "${CLAUDE_PLUGIN_ROOT}/scripts/faz/faz.py" durum`
- **Konusma ozeti:** bu konusmada ne yapildi, ne yarim kaldi

## 2. Karar ve Hatalari Isle

Bu konusmada bir karar verildiyse ya da bir hata cozulduyse, once onlari
deftere yaz - durum ozeti gecicidir, defter kalicidir:

```bash
D="${CLAUDE_PLUGIN_ROOT}/scripts/hafiza/defter.py"

python "$D" karar ekle "<baslik>" "<gerekce>"
python "$D" hata ekle "<belirti>" "<cozum>" --nerede "<dosya ya da katman>"
```

**Gerekce olmadan karar yazma.** "Ne" olmadan gecmis anlamsiz, "neden"
olmadan ogretici degildir.

## 3. Oturumu Kapat

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/hafiza/oturum.py" bitir \
  --not "<bu oturumda ne yapildi>" \
  --sirada "<bir sonraki konusmada ne yapilacak>"
```

Bu komut hem `hafiza/durum.md` dosyasini yeniler hem de oturumun tam
ozetini `hafiza/oturumlar/` altina yazar.

`$ARGUMENTS` verilmisse devir notuna ekle.

**Sirada ne var** alanini bos birakma. Yarim kalan is varsa dosya yolu ve
satir numarasiyla yaz - bir sonraki oturum aramakla vakit kaybetmesin.

## 4. Commit + Push

```bash
git add -A
git commit -m "Durum kaydi: <kisa ozet>"
git push
```

Push basarisiz olursa sebebini soyle, sessizce gecme.

Framework komutlarinda degisiklik yapildiysa ve calisilan proje framework
deposu DEGILSE, o degisiklik framework deposuna ayrica islenmeli -
kullaniciya hatirlat, kendin kopyalama.

## 5. Kullaniciya Bildir

```
DURUM KAYDEDILDI
  Dosya   : hafiza/durum.md
  Oturum  : hafiza/oturumlar/<tarih>-<no>.md
  Yapilan : <n> is
  Sirada  : <ilk madde>
```

## KURALLAR

- Durum dosyasini oturum katmani yazar; elle duzenleme
- Detayli ol ama gereksiz uzatma
- Yarim kalan isler icin dosya yolu ve satir numarasi ver
- Kasa dosyalarini ve sirlari kayda gecirme
