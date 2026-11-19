from pathlib import Path
import json,sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))

@pytest.fixture
def config():
    return json.loads((Path(__file__).resolve().parents[1]/'config.json').read_text())
