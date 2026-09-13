"""File picker variants with hidden filesystem entries visible by default."""

from textual_fspicker import FileOpen as _FileOpen
from textual_fspicker import FileSave as _FileSave
from textual_fspicker import SelectDirectory as _SelectDirectory
from textual_fspicker.parts.directory_navigation import DirectoryNavigation


class FileOpen(_FileOpen):
    """Open-file picker that shows hidden files and folders."""

    def on_mount(self) -> None:
        super().on_mount()
        self.query_one(DirectoryNavigation).show_hidden = True


class FileSave(_FileSave):
    """Save-file picker that shows hidden files and folders."""

    def on_mount(self) -> None:
        super().on_mount()
        self.query_one(DirectoryNavigation).show_hidden = True


class SelectDirectory(_SelectDirectory):
    """Directory picker that shows hidden folders."""

    def on_mount(self) -> None:
        super().on_mount()
        self.query_one(DirectoryNavigation).show_hidden = True
