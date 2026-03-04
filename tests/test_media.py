import time
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from core.media import (
    get_temp_dir,
    transcribe_voice,
    process_photo,
    process_document,
    cleanup_old_files,
)


def test_get_temp_dir_creates_directory():
    with patch("core.media._TEMP_DIR", None):
        d = get_temp_dir()
        assert d.exists()
        assert d.is_dir()


@pytest.mark.asyncio
async def test_transcribe_voice_ffmpeg_failure(tmp_path):
    ogg = tmp_path / "test.ogg"
    ogg.write_bytes(b"not real audio")

    with patch("asyncio.create_subprocess_exec") as mock_exec:
        proc = AsyncMock()
        proc.communicate.return_value = (b"", b"error")
        proc.returncode = 1
        mock_exec.return_value = proc

        result = await transcribe_voice(ogg)
    assert "failed" in result.lower()


@pytest.mark.asyncio
async def test_transcribe_voice_no_whisper(tmp_path):
    ogg = tmp_path / "test.ogg"
    ogg.write_bytes(b"not real audio")

    with patch("asyncio.create_subprocess_exec") as mock_exec:
        proc = AsyncMock()
        proc.communicate.return_value = (b"", b"")
        proc.returncode = 0
        mock_exec.return_value = proc

        # Simulate ImportError for faster_whisper
        with patch.dict("sys.modules", {"faster_whisper": None}):
            with patch("builtins.__import__", side_effect=ImportError("no whisper")):
                result = await transcribe_voice(ogg)
    assert "faster-whisper" in result.lower() or "voice" in result.lower()


@pytest.mark.asyncio
async def test_process_photo():
    mock_file = MagicMock()
    mock_tg_file = AsyncMock()
    mock_file.get_file = AsyncMock(return_value=mock_tg_file)
    mock_tg_file.download_to_drive = AsyncMock()

    with patch("core.media.get_temp_dir") as mock_dir:
        tmp = Path("/tmp/lobsterbot_test")
        tmp.mkdir(exist_ok=True)
        mock_dir.return_value = tmp

        prompt, path = await process_photo(mock_file, caption="Look at this")

    assert "photo" in prompt.lower()
    assert "Look at this" in prompt
    mock_tg_file.download_to_drive.assert_called_once()


@pytest.mark.asyncio
async def test_process_document():
    mock_file = MagicMock()
    mock_file.file_name = "report.pdf"
    mock_tg_file = AsyncMock()
    mock_file.get_file = AsyncMock(return_value=mock_tg_file)
    mock_tg_file.download_to_drive = AsyncMock()

    with patch("core.media.get_temp_dir") as mock_dir:
        tmp = Path("/tmp/lobsterbot_test")
        tmp.mkdir(exist_ok=True)
        mock_dir.return_value = tmp

        prompt, path = await process_document(mock_file, caption="Monthly report")

    assert "document" in prompt.lower()
    assert "report.pdf" in str(path)
    assert "Monthly report" in prompt


def test_cleanup_old_files(tmp_path):
    with patch("core.media.get_temp_dir", return_value=tmp_path):
        old_file = tmp_path / "old.txt"
        old_file.write_text("old")
        import os
        os.utime(old_file, (time.time() - 7200, time.time() - 7200))

        new_file = tmp_path / "new.txt"
        new_file.write_text("new")

        removed = cleanup_old_files()

    assert removed == 1
    assert not old_file.exists()
    assert new_file.exists()
