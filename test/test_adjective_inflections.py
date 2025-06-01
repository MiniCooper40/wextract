import pytest
from src.wiktionary_parser import NodeType, parse_itwiktionary_text
import os

file_dir_path = os.path.dirname(os.path.abspath(__file__))
resource_dir_path = os.path.join(file_dir_path, "resources")

@pytest.mark.parametrize("title, expected_forms", [
    ("verde", [{
        "ms": "verde",
        "fs": "verde",
        "mp": "verdi",
        "fp": "verdi",
        "self": "mfs",
        "gender_invariant": True,
        "number_invariant": False,
    }]),
    ("antracite", [{
        "ms": "antracite",
        "fs": None,
        "mp": "antraciti",
        "fp": None,
        "self": "ms",
        "gender_invariant": False,
        "number_invariant": False,
    }]),
])
def test_parse_wiktionary_adjective_text(title, expected_forms):
    with open(os.path.join(resource_dir_path, f"{title}.txt"), "r", encoding="utf-8") as file:
        text = file.read()
    result = parse_itwiktionary_text(title, text)
    assert len(result[NodeType.AGGETTIVO.english_translation]) > 0, "No aggettivo sections found"
    for i, (aggettivo, expected_form) in enumerate(zip(result[NodeType.AGGETTIVO.english_translation], expected_forms)):
        assert aggettivo["forms"] == expected_form, (
            f"Mismatch in section {i} for '{title}':\n"
            f"Expected: {expected_form}\n"
            f"Got:      {aggettivo['forms']}"
        )
