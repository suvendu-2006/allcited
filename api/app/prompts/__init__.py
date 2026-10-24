import hashlib
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).resolve().parent


class PromptRegistry:
    """
    Prompt registry managing versioned markdown prompt files.
    Calculates SHA-256 hashes dynamically and logs active prompt versions per pipeline run.
    """

    def __init__(self, prompts_dir: Optional[Path] = None):
        self.prompts_dir = prompts_dir or PROMPTS_DIR
        self._last_hashes: Dict[str, str] = {}

    def get_prompt(self, name: str, **kwargs) -> Tuple[str, str]:
        """
        Load prompt template from disk, compute its SHA-256 hash, and format with kwargs.

        Returns:
            Tuple[formatted_text, sha256_hash]
        """
        filename = f"{name}.md" if not name.endswith(".md") else name
        filepath = self.prompts_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(
                f"Prompt template '{filename}' not found in registry at {self.prompts_dir}"
            )

        raw_content = filepath.read_text(encoding="utf-8").strip()
        h = hashlib.sha256(raw_content.encode("utf-8")).hexdigest()[:12]

        self._last_hashes[name] = h
        logger.info("Prompt '%s' active hash: %s", name, h)

        if kwargs:
            formatted = raw_content.format(**kwargs)
        else:
            formatted = raw_content

        return formatted, h

    def get_prompt_text(self, name: str, **kwargs) -> str:
        text, _ = self.get_prompt(name, **kwargs)
        return text

    def get_hash(self, name: str) -> str:
        _, h = self.get_prompt(name)
        return h


_PROMPT_REGISTRY: Optional[PromptRegistry] = None


def get_prompt_registry() -> PromptRegistry:
    global _PROMPT_REGISTRY
    if _PROMPT_REGISTRY is None:
        _PROMPT_REGISTRY = PromptRegistry()
    return _PROMPT_REGISTRY


def get_prompt(name: str, **kwargs) -> Tuple[str, str]:
    return get_prompt_registry().get_prompt(name, **kwargs)


def get_prompt_text(name: str, **kwargs) -> str:
    return get_prompt_registry().get_prompt_text(name, **kwargs)
