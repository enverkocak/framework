---
name: index-rehber
description: Framework'te hangi komutlarin, becerilerin, ajanlarin ve korumalarin bulundugunu listeler ve tek tek anlatir. Kullanici "hangi komutlar var", "ne yapabiliyorsun", "bu komut ne ise yarar", "nasil kullanilir", "komut listesi", "rehber", "yardim", "index" derse ya da bir komutun adini sorarsa - acikca istemese bile - bu beceriyi kullan. Yeni bir isin hangi komutla yapilacagi belirsizse yine buraya bak.
---

# Komut rehberi

Bu beceri, framework'ün içinde ne olduğunu bilir ve anlatır.

## Temel kural

Liste **elle tutulmaz**. Her şey dosyalardan otomatik üretilir:

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/index-uret.py"
```

Bu üreteç şunları tarar:

| Kaynak | Ne bulur |
|--------|----------|
| `commands/*.md` | Eğik çizgi komutları |
| `skills/*/SKILL.md` | Beceriler |
| `agents/*.md` | Ajanlar |
| `hooks/*.py` | Korumalar |

Her dosyanın ön bilgisindeki `description` alanı açıklama olarak kullanılır.
Ön bilgi yoksa dosyanın ilk anlamlı satırı alınır.

## Üç kullanım biçimi

### 1. Tüm rehber
Kullanıcı "komutlar", "ne yapabiliyorsun", "rehber" derse:
üreteci çalıştır, çıktıyı kategorili tablolar hâlinde göster.

### 2. Tek komut
Kullanıcı bir komut adı sorarsa (`/index panel`, "panel ne işe yarar"):
`commands/<ad>.md` dosyasını oku ve şu düzende anlat:

- **Ne yapar** — tek cümle
- **Ne zaman kullanılır** — hangi ihtiyaçta
- **Kullanım** — çağırma biçimi, argümanlar
- **Örnek** — gerçek bir kullanım
- **İlgili komutlar**

### 3. İş tarifinden komut bulma
Kullanıcı ne yapmak istediğini anlatıyor ama komut adını bilmiyorsa
(“şunu nasıl yaparım?”): `--json` çıktısını al, açıklamalarda ara,
en uygun 2-3 komudu gerekçesiyle öner.

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/index-uret.py" --json
```

## Dil

Bütün başlıklar ve etiketler `diller/<kod>.json` dosyasından gelir.
Etkin dil `scripts/ortak/ayarlar.py` üzerinden okunur (varsayılan: Türkçe).
Metin koda gömülmez — yeni dil eklemek tek dosya çevirmekten ibarettir.

## Yazım kuralı

Kullanıcıya gösterilen metinlerde Türkçe karakterler tam kullanılır: ö, ç, ü, ğ, ı, ş, İ.
Komut ve klasör adlarında kullanılmaz.
