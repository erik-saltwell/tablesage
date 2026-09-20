"""Populate the documentation deployment with fictional, offline screenshot fixtures.

Run with the installed TableSage Python:
    python scripts/seed_docs_data.py --cwd .for-docs

Requires an initialized, empty deployment on the first run. Subsequent runs verify
the marked fixture without overwriting edits. Audio is silence, not a recording of
the authored dialogue; do not use it for transcription or speaker-ID evaluation.
No provider calls or real voice profiles are created.
"""

from __future__ import annotations

import argparse
import hashlib
import sqlite3
import wave
from datetime import UTC, datetime
from pathlib import Path

from seed_sample_data import _ensure_glossary_entry, seed
from sqlmodel import Session as DatabaseSession
from tablesage_application import Application
from tablesage_application.paths import ArtifactName
from tablesage_application.session_pipeline.artifact_graph import ArtifactStatus
from tablesage_application.session_pipeline.generate_ledger import Attendee, Ledger
from tablesage_application.session_pipeline.generate_player_introductions import (
    PlayerIntroduction,
    PlayerIntroductions,
    validate_player_introductions,
)
from tablesage_application.session_pipeline.role_transcript import RoleTranscript, RoleTranscriptUtterance
from tablesage_application.session_pipeline.scene_breakdown import Scene, SceneBreakdownContent, persist_ledger_pair
from tablesage_application.session_pipeline.transcript_sections import (
    InclusiveUtteranceRange,
    TranscriptSectionsGenerationResponse,
    load_current_transcript_sections,
    persist_transcript_sections,
)
from tablesage_model.model import Session as GameSession
from tablesage_model.setup import create_engine
from tablesage_tools.model import Transcript
from tablesage_tools.model.transcript import TranscriptionWord, Utterance

GM = "Game Master"
PLAYERS = {GM: "Alice", "Thorgrim": "Bob", "Lyra": "Priya"}
INTRODUCTIONS = [
    PlayerIntroduction(character="Thorgrim", description="A dwarven shieldbearer searching for his missing sister, Dagna."),
    PlayerIntroduction(character="Lyra", description="An elven cartographer tracing the lost waterways beneath Ironhold."),
]

# Each scene's entries are (role, established fact/action). These authored fixtures
# deliberately keep transcript, Ledger, scene coverage, and summaries aligned.
STORIES = [
    {
        "opening": "Thorgrim and Lyra stand at Ironhold's sealed lower gate. Three miners have vanished beyond it.",
        "ending": "The party has rescued Dagna and the miners, but the lower cistern is rising behind a sealed bronze door.",
        "scenes": [
            {
                "title": "A promise at the lower gate",
                "location": "Ironhold's lower gate",
                "participants": ["Thorgrim", "Lyra", "Warden Brinna"],
                "situation": "The lower tunnels are sealed while three miners remain missing.",
                "outcome": "Brinna opens the gate after Thorgrim promises to bring the miners home.",
                "carry_forward": [
                    "Thorgrim promised Brinna that he would bring all three miners home.",
                    "Brinna lent the party a brass survey lantern that reveals old water-level marks.",
                ],
                "signature_detail": "Blue flame catches on the lantern's dented brass rim.",
                "entries": [
                    (GM, "Warden Brinna guards Ironhold's lower gate; three miners, including Dagna, are missing below."),
                    ("Thorgrim", "promises Brinna that he will bring all three miners home"),
                    (GM, "Brinna opens the gate and lends the party a brass survey lantern that reveals old water-level marks."),
                    (GM, "Blue flame catches on the lantern's dented brass rim."),
                    ("Lyra", "maps the water-level marks leading toward the abandoned pump house"),
                ],
            },
            {
                "title": "Voices behind the fallen beam",
                "location": "Abandoned pump house",
                "participants": ["Thorgrim", "Lyra", "Dagna", "Two miners"],
                "situation": "A fallen beam traps Dagna and two miners beside a rising cistern.",
                "outcome": "The party frees the miners and sends them to Brinna, then investigates the bronze door.",
                "carry_forward": [
                    "Dagna heard three measured knocks from behind the bronze door.",
                    "Water is still rising in the lower cistern.",
                ],
                "signature_detail": "Three measured knocks sound through the bronze door.",
                "entries": [
                    (GM, "Dagna and two miners are trapped behind a fallen beam beside the lower cistern."),
                    ("Thorgrim", "lifts the beam while Lyra guides the three miners to safety"),
                    (GM, "Dagna says she heard three measured knocks from behind a bronze door; water is still rising."),
                    ("Lyra", "marks the safe route and sends the rescued miners back to Brinna"),
                    (GM, "Three measured knocks sound through the bronze door as the party approaches."),
                ],
            },
        ],
    },
    {
        "opening": "Thorgrim and Lyra face the bronze door beside the rising lower cistern, with Brinna's survey lantern in hand.",
        "ending": "The party has an alliance with the Deep Kin and evidence that someone in Ironhold ordered the cistern flooded.",
        "scenes": [
            {
                "title": "An answer in three knocks",
                "location": "Bronze cistern door",
                "participants": ["Thorgrim", "Lyra", "Sella Reedhand"],
                "situation": "Someone on the far side of the door is signaling while the water rises.",
                "outcome": "The party meets Sella and agrees to help the Deep Kin repair their shared floodgate.",
                "carry_forward": [
                    "Three knocks are the Deep Kin's request for safe passage.",
                    "Sella will guide the party if they help repair the floodgate.",
                ],
                "signature_detail": "Sella's reed-woven glove drips onto the bronze threshold.",
                "entries": [
                    ("Thorgrim", "answers the signal with three knocks"),
                    (GM, "Sella Reedhand opens the door; her reed-woven glove drips onto the bronze threshold."),
                    (GM, "Sella explains that three knocks ask for safe passage and identifies herself as a Deep Kin engineer."),
                    ("Lyra", "agrees to help repair the floodgate in exchange for Sella's guidance"),
                    (GM, "Sella accepts and leads the party toward the broken floodgate."),
                ],
            },
            {
                "title": "The lantern reveals a second channel",
                "location": "Deep Kin floodgate",
                "participants": ["Thorgrim", "Lyra", "Sella Reedhand"],
                "situation": "The main gate is jammed, and the cistern threatens both communities.",
                "outcome": "Lyra discovers an overflow channel, Thorgrim opens it, and Sella finds a forged maintenance order.",
                "carry_forward": [
                    "The overflow channel temporarily lowers the water.",
                    "A maintenance order bears Regent Orvek's seal.",
                    "Sella says the order instructed the engineers to jam the main floodgate.",
                ],
                "signature_detail": "The lantern's blue light reveals a channel erased from modern maps.",
                "entries": [
                    ("Lyra", "holds the survey lantern against the wall and discovers an overflow channel erased from modern maps"),
                    ("Thorgrim", "opens the overflow sluice, temporarily lowering the water"),
                    (GM, "Sella finds a maintenance order bearing Regent Orvek's seal."),
                    (GM, "Sella says the order instructed the engineers to jam the main floodgate; she believes it was forged."),
                    ("Lyra", "keeps the maintenance order to compare with the records in Ironhold"),
                ],
            },
        ],
    },
    {
        "opening": "Thorgrim and Lyra return to Ironhold with Sella and the suspicious maintenance order bearing Regent Orvek's seal.",
        "ending": "Brinna holds the forged order. The party and Sella wait outside the council chamber while Orvek prepares to speak.",
        "scenes": [
            {
                "title": "A debt repaid at the gate",
                "location": "Ironhold's lower gate",
                "participants": ["Thorgrim", "Lyra", "Sella Reedhand", "Warden Brinna", "Dagna"],
                "situation": "The gate guards refuse to admit Sella, a member of the Deep Kin.",
                "outcome": "Dagna confirms the rescue and Brinna admits Sella under her protection.",
                "carry_forward": [
                    "Brinna has publicly promised to protect Sella inside Ironhold.",
                    "Dagna can testify that the Deep Kin did not trap the miners.",
                ],
                "signature_detail": "Dagna ties a strip of her miner's scarf around Thorgrim's shield.",
                "entries": [
                    (GM, "The gate guards refuse to admit Sella because she belongs to the Deep Kin."),
                    ("Thorgrim", "asks Brinna to honor their agreement and hear Sella's account"),
                    (
                        GM,
                        "Dagna confirms the rescue and says the Deep Kin did not trap the miners. "
                        "She ties her scarf around Thorgrim's shield.",
                    ),
                    (GM, "Brinna publicly promises to protect Sella and admits her to Ironhold."),
                    ("Lyra", "asks Brinna to compare the maintenance order with the council archive"),
                ],
            },
            {
                "title": "The wrong mountain on the seal",
                "location": "Council archive",
                "participants": ["Thorgrim", "Lyra", "Sella Reedhand", "Warden Brinna"],
                "situation": "The party must determine whether the floodgate order really came from the regent.",
                "outcome": "The archive proves the seal was copied from an obsolete design, and Brinna calls for a council hearing.",
                "carry_forward": [
                    "The order's seal shows two mountain peaks; Orvek's current seal has three.",
                    "The author of the forged order remains unknown.",
                    "Orvek is about to speak at a council hearing.",
                ],
                "signature_detail": "Two mountain peaks on the forgery, three on the current seal.",
                "entries": [
                    ("Lyra", "compares the order's two-peaked seal with a current council order showing three peaks"),
                    (GM, "Brinna confirms that the two-peaked design was retired ten years ago; the maintenance order is forged."),
                    ("Thorgrim", "asks for a council hearing with Sella as a witness"),
                    (GM, "Brinna keeps the forged order as evidence and arranges a hearing; its author remains unknown."),
                    (GM, "The party and Sella wait outside the council chamber while Regent Orvek prepares to speak."),
                ],
            },
        ],
    },
]


def write_session(app: Application, game_session: GameSession, story: dict, previous_recap: str) -> str:
    folder = app.session_folder(game_session.id)
    if any(folder.iterdir()):
        raise ValueError(f"Refusing to overwrite existing session files: {folder}")
    dialogue = [(intro.character, f"I'm playing {intro.character}. {intro.description}") for intro in INTRODUCTIONS]
    dialogue.append((GM, story["opening"]))
    entries = [{"type": "narration", "source": GM, "fact": story["opening"]}]
    scenes = []
    for index, scene_data in enumerate(story["scenes"]):
        start = 0 if index == 0 else len(entries)
        for role, text in scene_data["entries"]:
            dialogue.append((role, text if role == GM else f"{role} {text.removesuffix('.')}."))
            entries.append(
                {"type": "narration", "source": role, "fact": text}
                if role == GM
                else {"type": "action", "source": role, "entity": role, "action": text}
            )
        scenes.append(
            Scene(
                **{key: value for key, value in scene_data.items() if key != "entries"},
                ledger_ranges=[{"start_index": start, "end_index": len(entries) - 1}],
            )
        )

    utterances = []
    position = 0.0
    for role, text in dialogue:
        words = []
        for token in text.split():
            words.append(TranscriptionWord(text=token, type="word", start=position, end=position + 0.3, speaker=PLAYERS[role]))
            position += 0.35
        utterances.append(Utterance(speaker=PLAYERS[role], start=words[0].start, end=words[-1].end, words=words, punctuated_text=text))
        position += 1.0

    with wave.open(str(folder / "input_audio.wav"), "wb") as audio:
        audio.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
        audio.writeframes(b"\0\0" * int((position + 1) * 16000))
    transcript = Transcript(utterances=utterances)
    transcript.save(folder / "transcript.json")
    (folder / "transcript.md").write_text(
        "# Transcript\n\n" + "\n\n".join(f"**{u.speaker}:** {u.punctuated_text}" for u in utterances) + "\n", encoding="utf-8"
    )
    transcript.save(folder / "transcript_reviewed.json")
    role_path = folder / "role_transcript.json"
    RoleTranscript(utterances=[RoleTranscriptUtterance(index=i, speaker=role, text=text) for i, (role, text) in enumerate(dialogue)]).save(
        role_path
    )
    persist_transcript_sections(
        TranscriptSectionsGenerationResponse(
            scratchpad="Authored documentation fixture.",
            recap_range=None,
            introduction_range=InclusiveUtteranceRange(start_index=0, end_index=1),
            starting_context_range=InclusiveUtteranceRange(start_index=2, end_index=2),
            session_start_index=2,
        ),
        role_path,
        folder / "transcript_sections.json",
    )
    attendees = tuple(Attendee(player_name=a.player_name, roles=a.roles) for a in app.list_attendance(game_session.id))
    ledger = Ledger(
        session_id=game_session.id,
        session_name=game_session.name,
        attendees=attendees,
        starting_situation=story["opening"],
        utterances=entries,
    )
    persist_ledger_pair(ledger, SceneBreakdownContent(ending_situation=story["ending"], scenes=scenes), folder)
    introductions = PlayerIntroductions(session_id=game_session.id, introductions=INTRODUCTIONS)
    introductions.save(folder / "player_introductions.json")
    recap = "## Recap\n\n" + "\n".join(f"- {scene.outcome}" for scene in scenes) + f"\n- {story['ending']}\n"
    (folder / "recap_summary.md").write_text(recap, encoding="utf-8")
    summary = f"# {game_session.name}\n\n"
    if previous_recap:
        summary += previous_recap + "\n"
    summary += introductions.to_markdown() + "\n"
    for scene in scenes:
        summary += f"## {scene.title}\n\n{scene.situation} {scene.outcome}\n\n"
        summary += "\n".join(f"- {fact}" for fact in scene.carry_forward) + "\n\n"
    summary += f"## Where we left off\n\n{story['ending']}\n"
    (folder / "summary.md").write_text(summary, encoding="utf-8")
    return recap


def verify(app: Application) -> None:
    campaign = next(c for c in app.list_campaigns() if c.name == "Iron Pact")
    for game_session in app.list_sessions(campaign.id):
        folder = app.session_folder(game_session.id)
        load_current_transcript_sections(folder / "role_transcript.json", folder / "transcript_sections.json")
        ledger = Ledger.load(folder / "ledger.json")
        introductions = PlayerIntroductions.load(folder / "player_introductions.json")
        validate_player_introductions(introductions, ledger.attendees)
        Transcript.load(folder / "transcript.json")
        Transcript.load(folder / "transcript_reviewed.json")
        expected = set(ArtifactName) - {ArtifactName.TRANSCRIPT_BENCHMARK, ArtifactName.TRANSCRIPT_ROLES_TEXT}
        states = app.session_artifact_states(game_session.id)
        invalid = {name.value: states[name].value for name in expected if states[name] != ArtifactStatus.CURRENT}
        if invalid:
            raise ValueError(f"Invalid artifact states for {game_session.name}: {invalid}")
        export_count = len(app.exportable_artifacts(game_session.id))
        print(f"Verified {game_session.name}: {len(ledger.utterances)} Ledger entries; {export_count} exports")
    history = app.previously_on_history(campaign.id)
    for session in history.sessions:
        folder = app.session_folder(session.breakdown.session_id)
        if session.breakdown.ledger_sha256 != hashlib.sha256((folder / "ledger.json").read_bytes()).hexdigest():
            raise ValueError("Scene Breakdown provenance mismatch")
    recap = app.create_campaign_scene_recap(campaign.id)
    print(f"Campaign history ready: {len(history.sessions)} sessions, {len(recap.scenes)} scenes")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cwd", type=Path, required=True, help="Initialized documentation deployment directory")
    args = parser.parse_args()
    cwd = args.cwd.resolve(strict=True)
    database = cwd / ".tablesage" / "tablesage.db"
    marker = cwd / ".tablesage" / "docs-fixture.txt"
    if not database.is_file():
        parser.error("Initialize the documentation deployment with TableSage first.")
    if marker.is_file():
        verify(Application(cwd))
        print("Existing documentation fixture preserved; no data overwritten.")
        return
    with sqlite3.connect(f"file:{database}?mode=ro", uri=True) as connection:
        if any(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in ("campaign", "player", "session")):
            parser.error("First-run seeding requires an empty database; existing data was preserved.")
    if any(root.exists() and any(root.iterdir()) for root in (cwd / "campaigns", cwd / "players")):
        parser.error("First-run seeding requires empty campaign and player folders.")
    backup = database.with_name("tablesage.before-docs-seed.db")
    if backup.exists():
        parser.error(f"Backup already exists: {backup}; inspect before retrying.")
    with sqlite3.connect(database) as source, sqlite3.connect(backup) as target:
        source.backup(target)

    app = Application(cwd)
    seed(app)
    campaign = next(c for c in app.list_campaigns() if c.name == "Iron Pact")
    for term, description in [
        ("Warden Brinna", "Keeper of Ironhold's lower gate; she values promises kept."),
        ("Dagna", "Thorgrim's sister, one of the three rescued miners."),
        ("Sella Reedhand", "A Deep Kin engineer working to save the shared cistern."),
        ("Deep Kin", "The community maintaining the waterways beneath Ironhold."),
        ("Regent Orvek", "Ironhold's regent; his current seal bears three mountain peaks."),
        ("Survey lantern", "A brass lantern whose blue flame reveals old water-level marks."),
    ]:
        _ensure_glossary_entry(app, campaign, term, description)
    game_sessions = sorted(app.list_sessions(campaign.id), key=lambda s: s.sequence_number)
    previous_recap = ""
    for game_session, story in zip(game_sessions, STORIES, strict=True):
        previous_recap = write_session(app, game_session, story, previous_recap)
    engine = create_engine(database)
    with DatabaseSession(engine) as db:
        for game_session in game_sessions:
            record = db.get(GameSession, game_session.id)
            if record is None:
                raise ValueError("Seeded session disappeared")
            record.status = "processed"
            record.updated_at = datetime.now(UTC)
            db.add(record)
        db.commit()
    engine.dispose()
    verify(app)
    marker.write_text(
        "Fictional documentation fixture created by scripts/seed_docs_data.py.\n"
        "All dialogue and outputs are authored sample data, not generated processing results.\n"
        "input_audio.wav files contain silence only. No real voice profiles are included.\n"
        "Iron Pact: three completed sessions. Other campaigns: setup and draft examples.\n",
        encoding="utf-8",
    )
    print(f"Seeded {len(app.list_campaigns())} campaigns and {len(app.list_players())} fictional players in {cwd}")


if __name__ == "__main__":
    main()
