# 🆓 Verified Free Tier Models & Providers

Daftar ini dikurasi oleh komunitas untuk membantu pengguna X-GPT menemukan model gratis yang aktif dan stabil. 

> ⚠️ **DISCLAIMER:** Ketersediaan model free tier dapat berubah sewaktu-waktu tanpa pemberitahuan dari provider. Daftar ini bersifat informatif dan tidak menjamin akses permanen. Selalu verifikasi status terbaru di [OpenRouter Models](https://openrouter.ai/models?q=free).

## Cara Menambahkan Model Baru
Jika Anda menemukan model free tier baru yang berfungsi, silakan buka **Pull Request** dengan memperbarui tabel di bawah ini. Pastikan untuk:
1.  Menguji model tersebut secara langsung minimal 3 kali request.
2.  Tidak menyertakan API key pribadi di PR atau komentar.
3.  Mengisi kolom "Catatan" dengan informasi rate limit atau kualitas output jika diketahui.

## Daftar Terverifikasi (Terakhir Diupdate: 2026-06-15)

| Model ID | Provider | Status | Catatan |
|----------|----------|--------|---------|
| `qwen/qwen3-coder:free` | OpenRouter | ✅ Aktif | Stabil untuk coding, ~5 req/menit. Default X-GPT. |
| `deepseek/deepseek-chat:free` | OpenRouter | ✅ Aktif | Terbaik untuk general chat & reasoning. Sangat stabil. |
| `meta-llama/llama-3.3-70b-instruct:free` | OpenRouter | ⚠️ Sering Penuh | Coba ulang saat off-peak. Bagus untuk instruksi kompleks. |
| `google/gemini-2.0-flash-exp:free` | OpenRouter | ✅ Aktif | Konteks panjang, cepat, jarang kena rate limit. |
| `mistralai/mistral-small-3.1-24b-instruct:free` | OpenRouter | ✅ Aktif | Ringan dan cepat, cocok untuk tugas sederhana. |
| `nousresearch/hermes-3-llama-3.1-8b:free` | OpenRouter | ✅ Aktif | Alternatif ringan jika model besar down. |

## Model yang Pernah Aktif (Arsip)
Model di bawah ini pernah tersedia namun saat ini sering down atau dihapus provider. Gunakan hanya sebagai fallback terakhir.

| Model ID | Provider | Status Terakhir | Alasan Penurunan |
|----------|----------|-----------------|------------------|
| `openai/gpt-oss-120b:free` | OpenRouter | ❌ Down | Model ID tidak valid / dihapus. |
| `qwen/qwen-2.5-coder-32b-instruct:free` | OpenRouter | ❌ Down | Digantikan oleh versi Qwen3. |
| `qwen/qwen3-coder:free` | OpenRouter | ✅ Aktif | Stabil untuk coding, ~5 req/menit |
| `deepseek/deepseek-chat:free` | OpenRouter | ✅ Aktif | Terbaik untuk general chat |
| `meta-llama/llama-3.3-70b-instruct:free` | OpenRouter | ⚠️ Sering Penuh | Coba ulang saat off-peak |

## Tips Menggunakan Free Tier
1.  **Gunakan Fallback Chain:** X-GPT sudah dilengkapi fallback otomatis. Jika model utama kena 429, ia akan pindah ke model berikutnya di daftar ini.
2.  **Hormati Rate Limit:** Jangan spam request. Free tier adalah fasilitas komunitas.
3.  **Laporkan Masalah:** Jika model di atas tiba-tiba error, silakan buka Issue di GitHub dengan label `free-tier-update`.

## Aturan Kontribusi
-   **DILARANG KERAS** menyertakan API key pribadi di PR atau komentar.
-   Hanya tambahkan model yang **Telah Anda verifikasi sendiri** berfungsi dalam 24 jam terakhir.
-   Sertakan screenshot atau log terminal sebagai bukti jika memungkinkan.
-   Update status model yang sudah tidak tersedia menjadi ❌ Down alih-alih menghapusnya (agar history terjaga).
