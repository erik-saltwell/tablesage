from __future__ import annotations

# Fixed filenames within a session folder -- the filesystem is the only
# source of truth for artifact existence, there is no `session_artifact`
# table. See `.documentation/import_player_from_filesystem.md`'s sibling doc,
# `.documentation/session_detail_screen.md`.
INPUT_AUDIO_FILENAME = "input_audio.wav"
PROCESSED_SESSION_FILENAME = "processed_session.json"
SESSION_SUMMARY_FILENAME = "summary.md"

AUDIO_EXTENSIONS = frozenset({".wav", ".mp3", ".m4a", ".flac", ".ogg"})
