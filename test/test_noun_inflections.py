import pytest
from src.wiktionary_parser import NodeType, parse_itwiktionary_text
import os

file_dir_path = os.path.dirname(os.path.abspath(__file__))
resource_dir_path = os.path.join(file_dir_path, "resources")

@pytest.mark.parametrize("title, expected_forms", [
    ("fine", [
        {
        "ms": "fine",
        "fs": None,
        "mp": None,
        "fp": None,
        "self": "ms",
        "gender_invariant": False,
        "number_invariant": False,
        },
        {
        "ms": "fine",
        "fs": "fine",
        "mp": "fini",
        "fp": "fini",
        "self": "mfs",
        "gender_invariant": False,
        "number_invariant": False,
        }
        ]),
    ("ragazzo", [{
        "ms": "ragazzo",
        "fs": "ragazza",
        "mp": "ragazzi",
        "fp": "ragazze",
        "self": "ms",
        "gender_invariant": False,
        "number_invariant": False,
    }]),
    ("luce", [{
        "ms": None,
        "fs": "luce",
        "mp": None,
        "fp": "luci",
        "self": "fs",
        "gender_invariant": False,
        "number_invariant": False,
    }]),
    ("informatica", [{
        "ms": None,
        "fs": "informatica",
        "mp": None,
        "fp": "informatiche",
        "self": "fs",
        "gender_invariant": False,
        "number_invariant": False,
    }]),
    ("novembre", [{
        "ms": "novembre",
        "fs": None,
        "mp": "novembre",
        "fp": None,
        "self": "m",
        "number_invariant": True,
        "gender_invariant": False
    }])
])
def test_parse_wiktionary_text(title, expected_forms):
    with open(os.path.join(resource_dir_path, f"{title}.txt"), "r", encoding="utf-8") as file:
        text = file.read()
        
    result = parse_itwiktionary_text(title, text)
    
    assert len(result[NodeType.SOSTANTIVO.english_translation]) > 0, "No sostantivo sections found"
    for i, (sostantivo, expected_form) in enumerate(zip(result[NodeType.SOSTANTIVO.english_translation], expected_forms)):
        assert sostantivo["forms"] == expected_form, (
            f"Mismatch in section {i} for '{title}':\n"
            f"Expected: {expected_form}\n"
            f"Got:      {sostantivo['forms']}"
        )