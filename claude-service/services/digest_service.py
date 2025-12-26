#!/usr/bin/env python3
"""
Digest service for Claude Service.

Handles reading and processing digest files from MCP.
"""

import json
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from utils.execution_dir import ExecutionDirectory


logger = logging.getLogger("claude-service")


def read_digest_file(exec_dir: "ExecutionDirectory") -> dict | None:
    """Read the digest JSON file created by the MCP submit_digest tool.

    Args:
        exec_dir: The execution directory containing the digest file.

    Returns:
        Parsed digest dict if file exists, None otherwise.
    """
    digest_path = exec_dir.digest_path

    if not digest_path.exists():
        logger.warning("Digest file not found: %s", digest_path)
        return None

    try:
        with open(digest_path, encoding="utf-8") as f:
            digest = json.load(f)
        logger.info("Read digest from %s", digest_path)
        return digest
    except json.JSONDecodeError as e:
        logger.error("Failed to parse digest file %s: %s", digest_path, e)
        return None
    except Exception as e:
        logger.error("Failed to read digest file %s: %s", digest_path, e)
        return None
