import logging
import os

logger = logging.getLogger(__name__)


def save_to_vault(vault_path: str, filename: str, content: str) -> str:
    """
    Save markdown file to Obsidian Vault.
    Overwrites if file exists.
    Raises FileNotFoundError if vault_path doesn't exist.
    Returns full path of saved file.
    """
    if not os.path.isdir(vault_path):
        logger.error(f"Obsidian Vault path does not exist: {vault_path}")
        raise FileNotFoundError(f"Vault path does not exist: {vault_path}")

    file_path = os.path.join(vault_path, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    return file_path