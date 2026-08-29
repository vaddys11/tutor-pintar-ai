"""
llm.py — Wrapper pemanggilan AI lewat OpenRouter (OpenAI-compatible) dengan
Multi-Model Fallback.

PENTING: Katalog model gratis OpenRouter SERING BERUBAH (model dihapus/jadi
berpapa tanpa peringatan). Jadi daftar model gratis di sini diambil LIVE dari
endpoint /api/v1/models tiap ~1 jam (cache), bukan hardcode nama model —
supaya gak error 400/404 tiap kali OpenRouter rotasi katalog.
"""
import os
import time
import httpx
from openai import OpenAI, APIStatusError, APIConnectionError, RateLimitError

# Jaring pengaman terakhir kalau fetch live gagal total (misal jaringan mati).
# "openrouter/free" adalah router bawaan OpenRouter yang otomatis pilih model
# gratis yang lagi tersedia — jadi tetap valid walau katalog gratis berubah.
FALLBACK_FREE_MODELS = [
    {"id": "openrouter/free", "label": "OpenRouter Auto (Free Router)", "vision": True},
]

RETRYABLE_STATUS = {429, 502, 503}

_models_cache = {"data": None, "fetched_at": 0}
_CACHE_TTL_SECONDS = 3600  # refresh daftar tiap 1 jam


def get_openrouter_client() -> OpenAI | None:
    """Init client OpenRouter (format OpenAI-compatible). Return None kalau API key kosong."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return None
    return OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)


def fetch_free_models(api_key: str, force_refresh: bool = False) -> list[dict]:
    """
    Ambil daftar model gratis LANGSUNG dari OpenRouter (live), difilter:
    - pricing prompt & completion == 0
    - punya slug ':free'
    - output-nya teks (bukan model gambar/audio doang)

    Hasil di-cache 1 jam biar gak nge-fetch tiap pesan. Kalau fetch gagal,
    fallback ke cache lama (kalau ada) atau FALLBACK_FREE_MODELS.
    """
    now = time.time()
    if not force_refresh and _models_cache["data"] and (now - _models_cache["fetched_at"] < _CACHE_TTL_SECONDS):
        return _models_cache["data"]

    if not api_key:
        return FALLBACK_FREE_MODELS

    try:
        resp = httpx.get(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10,
        )
        resp.raise_for_status()
        raw_models = resp.json().get("data", [])

        models = []
        for m in raw_models:
            mid = m.get("id", "")
            if not mid.endswith(":free"):
                continue
            if mid.startswith("openrouter/"):
                continue  # router auto ditambah manual belakangan
            pricing = m.get("pricing", {})
            if pricing.get("prompt") != "0" or pricing.get("completion") != "0":
                continue
            arch = m.get("architecture", {})
            if "text" not in arch.get("output_modalities", []):
                continue  # skip model image-gen/audio-only
            vision = "image" in arch.get("input_modalities", [])
            models.append({"id": mid, "label": m.get("name", mid), "vision": vision})

        if not models:
            raise ValueError("Gak ada model gratis ditemukan dari live fetch")

        # Model vision duluan (lebih fleksibel buat semua jenis pesan)
        models.sort(key=lambda m: not m["vision"])

        # Router auto sebagai jaring pengaman terakhir di urutan paling bawah
        models.append({"id": "openrouter/free", "label": "OpenRouter Auto (Free Router)", "vision": True})

        _models_cache["data"] = models
        _models_cache["fetched_at"] = now
        return models

    except Exception as e:
        print(f"[llm] Gagal ambil daftar model gratis live: {e}")
        if _models_cache["data"]:
            return _models_cache["data"]
        return FALLBACK_FREE_MODELS


def _has_image(messages: list[dict]) -> bool:
    for msg in messages:
        if isinstance(msg.get("content"), list):
            if any(part.get("type") == "image_url" for part in msg["content"]):
                return True
    return False


def _strip_image_parts(messages: list[dict]) -> list[dict]:
    """Buang bagian gambar dari messages — dipakai buat model yang gak support vision."""
    cleaned = []
    for msg in messages:
        content = msg.get("content")
        if isinstance(content, list):
            text_only = "\n".join(p["text"] for p in content if p.get("type") == "text")
            cleaned.append({"role": msg["role"], "content": text_only})
        else:
            cleaned.append(msg)
    return cleaned


def _is_retryable_error(error: Exception) -> bool:
    """Cek apakah error layak failover ke model berikutnya (429/502/503, rate-limit, model gak valid/ditarik)."""
    if isinstance(error, RateLimitError):
        return True
    if isinstance(error, APIStatusError):
        # 400/404 juga di-treat retryable di sini: biasanya artinya model itu
        # sudah ditarik/diganti slug oleh OpenRouter, bukan salah kita.
        return error.status_code in RETRYABLE_STATUS or error.status_code in {400, 404}
    if isinstance(error, APIConnectionError):
        return True
    text = str(error).lower()
    return any(code in text for code in ["429", "502", "503", "400", "404", "rate limit", "rate-limit", "not a valid model", "unavailable"])


def generate_response_with_fallback(
    client: OpenAI, messages: list[dict], temperature: float = 0.6, free_models: list[dict] | None = None
) -> tuple[str | None, str | None]:
    """
    Panggil model gratis sesuai urutan prioritas (dari fetch_free_models, atau
    FALLBACK_FREE_MODELS kalau gak dikasih). Kalau satu model gagal — limit,
    error jaringan, ATAU model itu ternyata udah gak ada/berbayar lagi di
    OpenRouter — otomatis coba model berikutnya.

    Return: (teks_respons, label_model_yang_berhasil) — atau (None, None) kalau semua gagal.
    """
    if client is None:
        return None, None

    models_to_try = free_models if free_models else FALLBACK_FREE_MODELS
    image_present = _has_image(messages)
    last_error = None

    for model in models_to_try:
        payload = messages if not (image_present and not model["vision"]) else _strip_image_parts(messages)

        try:
            response = client.chat.completions.create(
                model=model["id"],
                messages=payload,
                temperature=temperature,
            )
            reply = response.choices[0].message.content
            if reply:
                return reply, model["label"]
            last_error = f"{model['id']}: respons kosong"
            continue

        except Exception as e:
            last_error = f"{model['id']}: {e}"
            print(f"[llm] Model '{model['id']}' gagal, failover ke model berikutnya: {e}")
            continue

    print(f"[llm] Semua model gratis gagal. Error terakhir: {last_error}")
    return None, None
