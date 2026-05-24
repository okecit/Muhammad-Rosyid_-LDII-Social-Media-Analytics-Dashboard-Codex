# Dashboard Sentimen Dakwah Digital Indonesia

Dashboard ini dibuat untuk membantu riset S3 Komunikasi Islam dalam membaca percakapan komentar YouTube tentang dakwah digital di Indonesia. Aplikasi memuat data komentar, mengklasifikasikan sentimen ke `positif`, `netral`, dan `negatif`, lalu menampilkan distribusi sentimen, tabel komentar, ringkasan per video, serta ringkasan analitik berbasis OpenAI API.

Proyek ini memiliki dua mode:

- `Streamlit lokal`: dashboard Python penuh untuk analisis lokal.
- `Vercel`: dashboard static frontend dengan Python serverless API, karena Streamlit tidak cocok dijalankan langsung di Vercel serverless.

## Struktur Proyek

```text
.
├── app/
│   └── main.py
├── api/
│   ├── _shared.py
│   ├── analyze.py
│   └── summary.py
├── public/
│   └── index.html
├── data/
│   ├── raw/
│   │   ├── youtube_comments.csv
│   │   ├── facebook_comments_post_1456866053136403.csv
│   │   ├── facebook_comments_post_1457059806450361.csv
│   │   └── facebook_comments_post_1457655263057482.csv
│   └── processed/
├── src/
│   ├── config.py
│   ├── data_loader.py
│   ├── openai_summary.py
│   └── sentiment.py
├── .streamlit/
│   └── config.toml
├── requirements.txt
├── requirements-streamlit.txt
├── runtime.txt
├── vercel.json
└── README.md
```

## Fitur

- Membaca CSV komentar YouTube dengan kolom `author`, `comment`, `type`, `voteCount`, `replyCount`, `publishedTimeText`, `hasCreatorHeart`, `authorIsChannelOwner`, `title`, dan `pageUrl`.
- Analisis sentimen Bahasa Indonesia di mode Streamlit menggunakan model Hugging Face `w11wo/indonesian-roberta-base-sentiment-classifier`.
- Fallback kamus sederhana bila model transformer belum tersedia atau gagal dimuat.
- Mode Vercel memakai sentimen kamus sederhana agar serverless ringan dan cepat.
- Pie chart distribusi sentimen.
- Tabel komentar lengkap dengan label sentimen.
- Ringkasan per video.
- Tombol `Generate AI Summary` untuk menghasilkan 5 poin ringkasan analitik dalam Bahasa Indonesia melalui OpenAI API.
- Unduh hasil klasifikasi sentimen CSV di mode Streamlit.

## Menjalankan Streamlit Lokal

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

3. Install dependensi Streamlit.

```bash
pip install -r requirements-streamlit.txt
```

Jika ingin memakai model transformer penuh, install PyTorch tambahan. Tanpa ini, dashboard tetap jalan memakai fallback kamus sederhana.

```bash
pip install -r requirements-transformer.txt
```

4. Atur OpenAI API key jika ingin memakai fitur ringkasan AI.

Windows PowerShell:

```powershell
$env:OPENAI_API_KEY="sk-proj-..."
$env:OPENAI_MODEL="gpt-4.1-mini"
```

macOS/Linux:

```bash
export OPENAI_API_KEY="sk-proj-..."
export OPENAI_MODEL="gpt-4.1-mini"
```

5. Jalankan dashboard.

```bash
streamlit run app/main.py
```

Dashboard lokal biasanya terbuka di:

```text
http://localhost:8501
```

## Deploy ke Vercel

Mode Vercel memakai:

- `public/index.html` untuk tampilan dashboard.
- `api/analyze.py` untuk membaca CSV dan menghitung sentimen.
- `api/summary.py` untuk memanggil OpenAI API.
- `requirements.txt` yang ringan, hanya untuk kebutuhan serverless API.

Langkah deploy:

1. Push folder proyek ini ke GitHub.
2. Buat project baru di Vercel dan pilih repository tersebut.
3. Pastikan framework preset dibiarkan sebagai `Other`.
4. Tambahkan Environment Variables di Vercel:

```text
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4.1-mini
```

5. Deploy.

Setelah deploy, halaman utama Vercel akan membuka dashboard. Tombol `Generate AI Summary` akan bekerja jika `OPENAI_API_KEY` sudah tersimpan di Vercel.

## Catatan Metodologi Sentimen

Model transformer Bahasa Indonesia di mode Streamlit lebih cocok untuk eksplorasi lokal karena dapat memakai paket besar seperti `torch` dan `transformers`. Untuk Vercel, analisis sentimen dibuat lebih ringan memakai kamus sederhana agar sesuai dengan batasan serverless.

Dalam konteks riset akademik, hasil klasifikasi otomatis sebaiknya diperlakukan sebagai pembacaan awal yang perlu divalidasi. Untuk disertasi atau artikel ilmiah, disarankan mengambil sampel komentar dari tiap kelas sentimen lalu melakukan validasi manual atau intercoder reliability.

## Tujuan Riset

Dashboard ini diarahkan untuk membantu eksplorasi awal tentang bagaimana audiens digital merespons konten dakwah di YouTube. Fokus analitik meliputi distribusi sentimen, komentar dengan interaksi tinggi, variasi respons antar video, serta isu-isu yang dapat ditindaklanjuti untuk analisis komunikasi Islam, dakwah digital, otoritas keagamaan, dan dinamika penerimaan publik di ruang media sosial.
