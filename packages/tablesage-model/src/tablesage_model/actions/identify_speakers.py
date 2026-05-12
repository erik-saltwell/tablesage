from __future__ import annotations
from ..settings import SpeakerIdentificationSettings
from pathlib import Path
from ..protocols import IncrementalProgressEvent, IncrementalProgressSink
from .. import paths

def identify_speakers(campaign_slug:str, session_slug:str, settings: SpeakerIdentificationSettings, sink:IncrementalProgressSink)->None:
    session_dir: Path = paths.session_dir(campaign_slug, session_slug)
    source_path: Path = paths.to_absolute(session_dir, settings.raw_audio_file)