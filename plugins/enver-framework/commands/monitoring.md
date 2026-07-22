---
description: Sunucu sagligi, API uptime, SSL sertifika, CPU/RAM/disk, PM2 ve DB baglanti kontrolu
argument-hint: Opsiyonel - bos birak = menu, veya direkt (health, cpu, pm2, ssl, db, uptime)
---

# Monitoring - Sunucu Sagligi

Sunucu ve uygulama saglik kontrollerini yapar.

## MENU (arguman yoksa AskUserQuestion ile goster)

```
[1] Genel Bakis        Tek seferde tum kontroller
[2] API Health         /api/health + response time
[3] Sunucu Kaynaklari  CPU, RAM, disk kullanimi
[4] PM2 Durumu         Process listesi, uptime, restart
[5] DB Baglanti        PostgreSQL connection pool
[6] SSL Sertifika      Bitis tarihi (kac gun kaldi?)
[7] Uptime Kontrol     Tum domainlerin HTTP status
[0] ← Ana Menu
```

## NASIL CALISIR

SSH bilgisi `~/.claude/vault/sunucu.md` dosyasindan okunur.
Domain bilgisi projenin CLAUDE.md → `## DOMAIN YAPISI` bolumunden okunur.

### [1] Genel Bakis
Tum kontrolleri sirayla calistir, tek rapor ciktisi ver.

### [2] API Health
```bash
curl -w "\nResponse Time: %{time_total}s\n" -s https://api.[domain]/api/health
```

### [3] Sunucu Kaynaklari
```bash
ssh [sunucu] "free -h && echo '---' && df -h / && echo '---' && top -bn1 | head -5"
```

### [4] PM2 Durumu
```bash
ssh [sunucu] "pm2 list && pm2 jlist | head -100"
```

### [5] DB Baglanti
```bash
ssh [sunucu] "sudo -u postgres psql -d [db_name] -c 'SELECT count(*) as aktif_baglanti FROM pg_stat_activity WHERE state = \'active\''"
```

### [6] SSL Sertifika
```bash
echo | openssl s_client -connect [domain]:443 2>/dev/null | openssl x509 -noout -dates
```

### [7] Uptime Kontrol
Her domain icin: `curl -sI -o /dev/null -w "%{http_code}" https://[domain]`

## RAPOR
```
╔═══════════════════════════════════════════╗
║         MONITORING RAPORU                ║
╠═══════════════════════════════════════════╣
║  API:     ✅ 200 OK (145ms)             ║
║  CPU:     23% | RAM: 1.2/4 GB           ║
║  Disk:    45% (18/40 GB)                ║
║  PM2:     2 online, 0 error             ║
║  DB:      5/20 baglanti aktif           ║
║  SSL:     87 gun kaldi (15.06.2026)     ║
║  Uptime:  4/4 domain aktif              ║
╚═══════════════════════════════════════════╝
```

## KURALLAR
- SSH bilgisi vault'tan okunur
- Sunucuda sadece READ-ONLY komutlar calistirilir
- Kritik esiklerde uyari ver (disk >80%, RAM >90%, SSL <30 gun)
