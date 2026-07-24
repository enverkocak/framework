---
name: proje-devral
description: 'Zaten var olan bir projeyle calisilacaksa - eski bir site, devralinan bir musteri isi, uzun sure dokunulmamis bir depo - koda dokunmadan once bu beceriyi kullan. Kullanici "su projeyi devralalim", "bu eski site", "burayi bir incele", "ne yapiyor bu proje", "framework''e uyarla", "bu projeyi ogren" derse ya da cerceve dosyasi (CLAUDE.md, .claude/proje.json) olmayan bir dizinde is istenirse, acikca istemese bile devreye gir. Amac - bilmedigi bir kod tabaninda tahminle degisiklik yapmamak. Once taranir, ogrenilir, yaziya dokulur, ONAY alinir, ANCAK ONDAN SONRA uyarlanir.'
---

# Proje devralma

Sıfırdan yazılmayan projede en pahalı hata, kurulu düzeni görmeden
değişiklik yapmaktır. Var olan kod bir karar yığınıdır: her tuhaf duran
satırın arkasında çoğu zaman bir sebep vardır.

**Önce oku, sonra yaz.**

## Ne zaman devreye girer

- Çerçeve dosyası olmayan bir dizinde iş isteniyorsa
- Devralınan, uzun süre dokunulmamış ya da başkasının yazdığı bir proje
- "Bu proje ne yapıyor" sorusu

Tek dosyalık küçük bir düzeltme için gerekmez. Ölçüt: **projede ilk kez
çalışılıyorsa** devralma yapılır.

## Akış

Ayrıntılı adımlar `/proje-devral` komutundadır. Özet:

```bash
D="${CLAUDE_PLUGIN_ROOT}/scripts/projeler/devral.py"

python "$D" tara --yol "<kök>"     # hiçbir şey yazmaz
python "$D" plan --yol "<kök>"     # ne yapılacağını gösterir
python "$D" uygula --yol "<kök>" --onay
```

Arada, taramanın raporu üzerine beş `devralma-ajani` paralel çalışır:
`mimari`, `veri`, `surec`, `kurallar`, `yarim-is`.

## Değişmez kurallar

1. **Onaysız yazılmaz.** Tarama ve plan aşaması hiçbir dosyaya dokunmaz.
2. **Var olan dosyanın üzerine yazılmaz.** `CLAUDE.md` zaten varsa
   korunur; eksik olan tamamlanır.
3. **Sır değeri raporlanmaz.** Anahtar bulunursa yalnız yeri bildirilir.
4. **Tahmin, bilgi gibi sunulmaz.** Çıkarılan her alan işaretlidir.
5. **Kritik risk sessizce geçilmez.** Depoya girmiş sır dosyası varsa
   kapanışta tekrar söylenir.

## Sonrası

Devralma bitince proje çerçeveye bağlıdır: faz motoru `hafiza/faz-plani.json`
üzerinden yürür, oturum kaydı `hafiza/durum.md`'ye yazar. Buradan sonra
normal akış geçerlidir.

## İlgili

- `/proje-devral` — komutun tamamı
- `proje-kesif` — sıfırdan proje için, sorularla ilerler
- `/faz` — üretilen planı yürütür
