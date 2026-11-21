import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_game_logic_imports_without_pygame():
    """The rules layer must be usable headlessly, with no Pygame installed."""
    code = (
        "import sys\n"
        "import tetris.board, tetris.game, tetris.pieces, tetris.randomizer\n"
        "assert 'pygame' not in sys.modules, 'logic layer imported pygame'\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
