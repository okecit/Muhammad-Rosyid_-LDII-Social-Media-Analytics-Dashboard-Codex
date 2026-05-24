# Dashboard Sentimen Dakwah Digital Indonesia

Dashboard ini dibuat untuk membantu riset S3 Komunikasi Islam dalam membaca percakapan komentar YouTube tentang dakwah digital di Indonesia. Aplikasi memuat data komentar, mengklasifikasikan sentimen ke `positif`, `netral`, dan `negatif`, lalu menampilkan distribusi sentimen, tabel komentar, ringkasan per video, serta ringkasan analitik berbasis Claude API.

## Struktur Proyek

```text
.
├── app/
│   └── main.py
├── api/
│   └── index.py
├── data/
│   ├── raw/
│   │   ├── youtube_comments.csv
│   │   ├── facebook_comments_post_1456866053136403.csv
│   │   ├── facebook_comments_post_1457059806450361.csv
│   │   └── facebook_comments_post_1457655263057482.csv
│   └── processed/
├── src/
│   ├── claude_summary.py
│   ├── config.py
│   ├── data_loader.py
│   └── sentiment.py
├── .streamlit/
│   └── config.toml
├── requirements.txt
├── runtime.txt
├── vercel.json
└── README.md
```

## Fitur

- Membaca CSV komentar YouTube dengan kolom `author`, `comment`, `type`, `voteCount`, `replyCount`, `publishedTimeText`, `hasCreatorHeart`, `authorIsChannelOwner`, `title`, dan `pageUrl`.
- Analisis sentimen Bahasa Indonesia menggunakan model Hugging Face `w11wo/indonesian-roberta-base-sentiment-classifier`.
- Fallback kamus sederhana bila model transformer belum tersedia atau gagal dimuat.
- Pie chart distribusi sentimen.
- Tabel komentar lengkap dengan label sentimen dan skor keyakinan.
- Ringkasan per video.
- Tombol `Generate AI Summary` untuk menghasilkan 5 poin ringkasan analitik dalam Bahasa Indonesia melalui Claude API.
- Unduh hasil klasifikasi sentimen dalam format CSV.

## Cara Menjalankan Lokal

1. Buat virtual environment.

```bash
python -m venv .venv
```

2. Aktifkan virtual environment.

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

3. Install dependensi.

```bash
pip install -r requirements.txt
```

4. Atur Claude API key jika ingin memakai fitur ringkasan AI.

Windows PowerShell:

```powershell
$env:ANTHROPIC_API_KEY="sk-ant-api03-..."
$env:ANTHROPIC_MODEL="claude-sonnet-4-20250514"
```

macOS/Linux:

```bash
export ANTHROPIC_API_KEY="sk-ant-api03-..."
export ANTHROPIC_MODEL="claude-sonnet-4-20250514"
```

5. Jalankan dashboard.

```bash
streamlit run app/main.py
```

## Catatan Metodologi Sentimen

Model utama memakai transformer Bahasa Indonesia dari Hugging Face. Dalam konteks riset akademik, hasil klasifikasi otomatis sebaiknya diperlakukan sebagai pembacaan awal yang perlu divalidasi. Untuk disertasi atau artikel ilmiah, disarankan mengambil sampel komentar dari tiap kelas sentimen lalu melakukan validasi manual atau intercoder reliability.

Fallback kamus sederhana hanya digunakan bila model transformer tidak bisa dimuat, misalnya karena belum ada internet untuk mengunduh model atau perangkat tidak cukup kuat. Label dari fallback tidak sekuat model transformer dan tidak ideal dijadikan hasil final penelitian tanpa validasi.

## Deployment

### Streamlit Community Cloud atau Render

Platform yang paling cocok untuk aplikasi ini adalah Streamlit Community Cloud, Render, Railway, atau server Python biasa karena Streamlit memerlukan proses web server yang berjalan terus.

Perintah start:

```bash
streamlit run app/main.py --server.port $PORT --server.address 0.0.0.0
```

Environment variable yang dibutuhkan:

```text
ANTHROPIC_API_KEY
ANTHROPIC_MODEL=claude-sonnet-4-20250514
```

### Vercel

Repository ini menyertakan `vercel.json` dan `api/index.py` agar proyek tetap bisa dikenali oleh Vercel sebagai proyek Python. Namun, Vercel serverless tidak cocok untuk menjalankan Streamlit secara penuh karena proses Streamlit perlu server long-running dan model transformer bisa berukuran besar.

Jika target akhirnya wajib Vercel, pendekatan yang lebih tepat adalah memisahkan aplikasi menjadi frontend statis di Vercel dan backend Python API di platform lain. Untuk dashboard Streamlit apa adanya, gunakan Streamlit Community Cloud atau Render.

## Tujuan Riset

Dashboard ini diarahkan untuk membantu eksplorasi awal tentang bagaimana audiens digital merespons konten dakwah di YouTube. Fokus analitik meliputi distribusi sentimen, komentar dengan interaksi tinggi, variasi respons antar video, serta isu-isu yang dapat ditindaklanjuti untuk analisis komunikasi Islam, dakwah digital, otoritas keagamaan, dan dinamika penerimaan publik di ruang media sosial.
