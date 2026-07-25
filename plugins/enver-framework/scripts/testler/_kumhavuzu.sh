#!/usr/bin/env bash
# Kapı testleri için kum havuzu - gerçek hafıza kirlenmesin diye.
#
# SORUN
# Kapı testleri görev, karar, hata ve cihaz kaydı üretir. Bu kayıtlar
# gerçek hafızaya yazılınca "nerede kaldık" bilgisi test çöpünün altında
# kalır. Sürekli çöp üreten bir kayıt bir süre sonra hiç okunmaz ve asıl
# yakalaması gereken satırı da o gürültünün içinde kaçırırsın.
#
# ÇÖZÜM
# Hafıza betiklerinin tamamı yolu yollar.proje_kok() üzerinden çözer,
# o da CLAUDE_PROJECT_DIR ortam değişkenini tanır. Test yazan komutlar
# bu değişkenle çağrılınca gerçek hafızaya değil kum havuzuna yazar.
#
# Havuzun içine bir .claude işareti konur; böylece kök arama yukarı
# çıkıp gerçek depoyu bulmaz, havuzun kendisinde durur.
#
# KULLANIM
#   source "$P/scripts/testler/_kumhavuzu.sh"
#   kumhavuzu_ac "$KOK"
#   CLAUDE_PROJECT_DIR="$KUM" python "$P/scripts/hafiza/defter.py" karar ekle ...
#   [ -f "$KUM/hafiza/kararlar.md" ] && ...
#
# Yalnız YAZAN komutlar havuza yönlendirilir. Gerçek depoyu okuyan
# kontroller (dosya var mı, git yok sayıyor mu) olduğu gibi kalır -
# yoksa test ölçmesi gereken şeyi ölçmez.
#
# Geliştirici: Enver KOCAK

# Her koşu kendi havuzunu alır. Silme yapılmaz: kural gereği hiçbir veri
# silinmez, _calisma/ zaten geçici işlerin yeri ve depoya girmez.
kumhavuzu_ac() {
  local kok="${1:-$PWD}"
  KUM="$kok/_calisma/kapi-kumhavuzu/$(date +%Y%m%d-%H%M%S)-$$"
  mkdir -p "$KUM/.claude" "$KUM/hafiza/oturumlar" "$KUM/gunluk/ciktilar"
  export KUM
}
