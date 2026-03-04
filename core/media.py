import asyncio
import logging
import shutil
import tempfile
import time
from pathlib import Path

logger = logging.getLogger(__name__)

_TEMP_DIR: Path | None = None
_CLEANUP_AGE = 3600  # 1 hour


def get_temp_dir() -> Path:
    global _TEMP_DIR
    if _TEMP_DIR is None:
        _TEMP_DIR = Path(tempfile.mkdtemp(prefix="lobsterbot_"))
    _TEMP_DIR.mkdir(parents=True, exist_ok=True)
    return _TEMP_DIR


async def download_telegram_file(file_obj, dest: Path) -> Path:
    """Download a Telegram file object to a local path."""
    tg_file = await file_obj.get_file()
    await tg_file.download_to_drive(str(dest))
    return dest


async def transcribe_voice(ogg_path: Path) -> str:
    """Convert OGG voice message to text via ffmpeg + faster-whisper."""
    wav_path = ogg_path.with_suffix(".wav")

    # Convert OGG to WAV
    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", "-i", str(ogg_path), "-ar", "16000", "-ac", "1",
        "-f", "wav", str(wav_path), "-y",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        logger.error("ffmpeg failed: %s", stderr.decode()[:500])
        return "[Voice message — transcription failed]"

    try:
        from faster_whisper import WhisperModel
        model = WhisperModel("base", device="cpu", compute_type="int8")
        segments, _ = model.transcribe(str(wav_path))
        text = " ".join(seg.text.strip() for seg in segments)
        return text or "[Voice message — no speech detected]"
    except ImportError:
        logger.warning("faster-whisper not installed, falling back to file path")
        return f"[Voice message saved to {wav_path} — install faster-whisper for transcription]"
    finally:
        wav_path.unlink(missing_ok=True)


async def process_voice(voice_file) -> str:
    """Download and transcribe a voice message."""
    temp = get_temp_dir()
    ogg_path = temp / f"voice_{int(time.time() * 1000)}.ogg"
    await download_telegram_file(voice_file, ogg_path)

    try:
        return await transcribe_voice(ogg_path)
    finally:
        ogg_path.unlink(missing_ok=True)


async def process_photo(photo_file, caption: str = "") -> tuple[str, Path]:
    """Download a photo and return (prompt_text, file_path)."""
    temp = get_temp_dir()
    photo_path = temp / f"photo_{int(time.time() * 1000)}.jpg"
    await download_telegram_file(photo_file, photo_path)

    prompt = f"The user sent a photo at {photo_path}"
    if caption:
        prompt += f" with caption: {caption}"
    return prompt, photo_path


async def process_document(doc_file, caption: str = "") -> tuple[str, Path]:
    """Download a document and return (prompt_text, file_path)."""
    temp = get_temp_dir()
    filename = doc_file.file_name or f"doc_{int(time.time() * 1000)}"
    doc_path = temp / filename
    await download_telegram_file(doc_file, doc_path)

    prompt = f"The user sent a document at {doc_path}"
    if caption:
        prompt += f" with caption: {caption}"
    return prompt, doc_path


def cleanup_old_files():
    """Remove temp files older than _CLEANUP_AGE seconds."""
    temp = get_temp_dir()
    cutoff = time.time() - _CLEANUP_AGE
    removed = 0
    for f in temp.iterdir():
        if f.is_file() and f.stat().st_mtime < cutoff:
            f.unlink()
            removed += 1
    if removed:
        logger.info("Cleaned up %d old temp files", removed)
    return removed
