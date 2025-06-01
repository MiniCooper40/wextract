from pprint import pprint
import pytest
from src.wiktionary_parser import NodeType, parse_itwiktionary_text
import os

file_dir_path = os.path.dirname(os.path.abspath(__file__))
resource_dir_path = os.path.join(file_dir_path, "resources")

@pytest.mark.parametrize(
    "word,expected_antonyms",
    [
        ("luce", [
            {
                "words": ["oscurità", "buio", "notte", "tenebre", "ombra", "controluce"],
                "gloss": None
            },
            {
                "words": ["abisso"],
                "gloss": "senso figurato"
            }
        ]),
    ]
)
def test_parse_antonyms(word, expected_antonyms):
    with open(os.path.join(resource_dir_path, f"{word}.txt"), "r", encoding="utf-8") as file:
        text = file.read()
        
    result = parse_itwiktionary_text(word, text)
    
    print(f"Antonyms found: {result[NodeType.ANTONIMI.english_translation]}")
    assert len(result[NodeType.ANTONIMI.english_translation]) > 0, "No antonimi sections found"
    for expected_antonym_set in expected_antonyms:
        print(f"Checking antonym set: gloss: {expected_antonym_set['gloss']}, words: {sorted(expected_antonym_set['words'])}")
        assert any(sorted(actual_antonym_set["words"]) == sorted(expected_antonym_set["words"]) and actual_antonym_set["gloss"] == expected_antonym_set["gloss"] for actual_antonym_set in result[NodeType.ANTONIMI.english_translation]), (
            f"Mismatch in section for '{word}'"
        )
