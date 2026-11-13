from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.services.scanner.enhancement import OutputFilterMode


class PresetSettings(BaseModel):
    filter_mode: OutputFilterMode = OutputFilterMode.COLOR
    brightness: float = Field(0.0, ge=-100.0, le=100.0)
    contrast: float = Field(0.0, ge=-100.0, le=100.0)
    exposure: float = Field(0.0, ge=-2.0, le=2.0)
    shadows: float = Field(0.0, ge=0.0, le=100.0)
    highlights: float = Field(0.0, ge=-100.0, le=100.0)
    whites: float = Field(0.0, ge=0.0, le=100.0)
    blacks: float = Field(0.0, ge=0.0, le=100.0)
    gamma: float = Field(1.0, ge=0.4, le=2.5)
    sharpen: float = Field(0.3, ge=0.0, le=1.0)
    denoise: float = Field(0.2, ge=0.0, le=1.0)
    remove_shadows: bool = True
    preserve_color_stamps: bool = True
    dewarp_enabled: bool = False
    ocr_enabled: bool = True
    ocr_language: str = "eng"


class ScannerPreset(BaseModel):
    id: str
    name: str
    description: str
    is_builtin: bool = False
    version: int = 1
    settings: PresetSettings


BUILTIN_PRESETS: Dict[str, ScannerPreset] = {
    "auto": ScannerPreset(
        id="auto",
        name="Auto",
        description="Smart automatic detection of document type, geometry, and color balance.",
        is_builtin=True,
        version=1,
        settings=PresetSettings(
            filter_mode=OutputFilterMode.COLOR,
            brightness=0.0,
            contrast=10.0,
            whites=25.0,
            blacks=15.0,
            sharpen=0.35,
            denoise=0.2,
            remove_shadows=True,
            preserve_color_stamps=True,
            dewarp_enabled=False,
        ),
    ),
    "document": ScannerPreset(
        id="document",
        name="Document",
        description="Letters and paperwork. Crisp black text, pure white background, shadow removal.",
        is_builtin=True,
        version=1,
        settings=PresetSettings(
            filter_mode=OutputFilterMode.COLOR,
            brightness=5.0,
            contrast=20.0,
            whites=40.0,
            blacks=25.0,
            sharpen=0.45,
            denoise=0.25,
            remove_shadows=True,
            preserve_color_stamps=True,
            dewarp_enabled=False,
        ),
    ),
    "book": ScannerPreset(
        id="book",
        name="Book",
        description="Bound textbooks and notebooks. Curved-page dewarping and inner margin correction.",
        is_builtin=True,
        version=1,
        settings=PresetSettings(
            filter_mode=OutputFilterMode.COLOR,
            brightness=0.0,
            contrast=15.0,
            whites=30.0,
            blacks=20.0,
            sharpen=0.40,
            denoise=0.2,
            remove_shadows=True,
            preserve_color_stamps=True,
            dewarp_enabled=True,
        ),
    ),
    "receipt": ScannerPreset(
        id="receipt",
        name="Receipt",
        description="Thermal receipts and invoices. Preserves faint thermal ink and enhances small fonts.",
        is_builtin=True,
        version=1,
        settings=PresetSettings(
            filter_mode=OutputFilterMode.BW,
            brightness=-5.0,
            contrast=35.0,
            whites=20.0,
            blacks=45.0,
            gamma=0.85,  # Slightly darkens midtones so faint print is visible
            sharpen=0.55,
            denoise=0.1,
            remove_shadows=True,
            preserve_color_stamps=False,
            dewarp_enabled=False,
        ),
    ),
    "id_card": ScannerPreset(
        id="id_card",
        name="ID Card",
        description="Identification, badges, and business cards. Preserves true photo colors and fine security detail.",
        is_builtin=True,
        version=1,
        settings=PresetSettings(
            filter_mode=OutputFilterMode.COLOR,
            brightness=0.0,
            contrast=5.0,
            whites=10.0,
            blacks=10.0,
            sharpen=0.25,
            denoise=0.15,
            remove_shadows=False,
            preserve_color_stamps=True,
            dewarp_enabled=False,
        ),
    ),
    "photo_archive": ScannerPreset(
        id="photo_archive",
        name="Photo Archive",
        description="Printed photos, historical documents, and handwriting. Gentle, non-destructive natural balance.",
        is_builtin=True,
        version=1,
        settings=PresetSettings(
            filter_mode=OutputFilterMode.PHOTO,
            brightness=0.0,
            contrast=0.0,
            whites=0.0,
            blacks=0.0,
            gamma=1.0,
            sharpen=0.15,
            denoise=0.1,
            remove_shadows=False,
            preserve_color_stamps=True,
            dewarp_enabled=False,
        ),
    ),
}


class PresetStore:
    """Manages built-in and persistent custom presets."""

    def __init__(self, storage_path: Path | None = None):
        if storage_path is None:
            storage_path = Path(__file__).resolve().parent.parent.parent.parent / "storage" / "custom_presets.json"
        self.storage_path = storage_path
        self._custom_presets: Dict[str, ScannerPreset] = {}
        self._load()

    def _load(self) -> None:
        if self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text(encoding="utf-8"))
                for item in data:
                    preset = ScannerPreset.model_validate(item)
                    preset.is_builtin = False
                    self._custom_presets[preset.id] = preset
            except Exception:
                self._custom_presets = {}

    def _save(self) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = [p.model_dump() for p in self._custom_presets.values()]
        self.storage_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def list_all(self) -> List[ScannerPreset]:
        combined = list(BUILTIN_PRESETS.values()) + list(self._custom_presets.values())
        return combined

    def get(self, preset_id: str) -> Optional[ScannerPreset]:
        clean_id = preset_id.lower().strip()
        if clean_id in BUILTIN_PRESETS:
            return BUILTIN_PRESETS[clean_id]
        return self._custom_presets.get(clean_id)

    def save_custom(self, preset: ScannerPreset) -> ScannerPreset:
        clean_id = preset.id.lower().strip()
        if clean_id in BUILTIN_PRESETS:
            raise ValueError(f"Cannot overwrite built-in preset '{clean_id}'.")
        preset.is_builtin = False
        self._custom_presets[clean_id] = preset
        self._save()
        return preset

    def delete_custom(self, preset_id: str) -> bool:
        clean_id = preset_id.lower().strip()
        if clean_id in BUILTIN_PRESETS:
            raise ValueError(f"Cannot delete built-in preset '{clean_id}'.")
        if clean_id in self._custom_presets:
            del self._custom_presets[clean_id]
            self._save()
            return True
        return False


preset_store = PresetStore()

