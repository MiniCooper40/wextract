import pytest
from src.wiktionary_parser import NodeType, parse_itwiktionary_text
import os

file_dir_path = os.path.dirname(os.path.abspath(__file__))
resource_dir_path = os.path.join(file_dir_path, "resources")

@pytest.mark.parametrize(
    "word,expected_derivatives",
    [
        ("luce", [
            {
                "words": ["antelucano", "anno luce", "controluce", "paraluce", "sopraluce", "lucido"],
                "gloss": None
            },
        ]),
    ]
)
def test_parse_derivatives(word, expected_derivatives):
    with open(os.path.join(resource_dir_path, f"{word}.txt"), "r", encoding="utf-8") as file:
        text = file.read()
        
    result = parse_itwiktionary_text(word, text)
    
    print(f"Derivatives found: {result[NodeType.DERIVATIVE.english_translation]}")
    assert len(result[NodeType.DERIVATIVE.english_translation]) > 0, "No derivati sections found"
    for expected_derivative_set in expected_derivatives:
        print(f"Checking derivative set: gloss: {expected_derivative_set['gloss']}, words: {sorted(expected_derivative_set['words'])}")
        assert any(sorted(actual_derivative_set["words"]) == sorted(expected_derivative_set["words"]) and actual_derivative_set["gloss"] == expected_derivative_set["gloss"] for actual_derivative_set in result[NodeType.DERIVATIVE.english_translation]), (
            f"Mismatch in section for '{word}'"
        )
