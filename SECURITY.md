# Güvenlik / Security

## Türkçe

### Açık bildirme

Bir güvenlik açığı bulduysan **herkese açık konu (issue) açma.** Doğrudan yaz:

**mail@enverkocak.com**

Şunları ekle: açığın ne olduğu, nasıl tetiklendiği, etkisi. Makul sürede dönüş
yapılır ve düzeltme yayınlanınca bilgilendirilirsin.

### Bu çerçeve neyi korur

- **Kasa** — şifreler ve anahtarlar şifreli tutulur; koda sır yazılması engellenir.
- **Veri koruma** — silme engellenir, yıkıcı komutlar onay ister.
- **Depo gizliliği** — depo istemeden herkese açık yapılamaz.
- **Sunucu koruma** — tanımlı dizin dışına erişim engellenir.

Bu korumalar kancalarla zorlanır ve `tumunu-calistir.sh` ile denetlenir.

---

## English

### Reporting a vulnerability

If you find a security issue, **do not open a public issue.** Email directly:

**mail@enverkocak.com**

Include what the issue is, how it triggers, and its impact. You'll get a reply in
reasonable time and a note when a fix ships.

### What this framework protects

- **Vault** — passwords and keys are encrypted; secrets in code are blocked.
- **Data protection** — deletions blocked, destructive commands require confirmation.
- **Repo privacy** — a repository can't be made public by accident.
- **Server protection** — access outside declared directories is blocked.

These are enforced by hooks and verified by `tumunu-calistir.sh`.
