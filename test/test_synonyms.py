import pytest
from src.wiktionary_parser import NodeType, parse_itwiktionary_text
import os

file_dir_path = os.path.dirname(os.path.abspath(__file__))
resource_dir_path = os.path.join(file_dir_path, "resources")

@pytest.mark.parametrize(
    "word,expected_synsets",
    [
        ("luce", [
            {
                "words": ["radiazione luminosa", "energia elettrica"],
                "gloss": "fisica"
            },
            {
                "words": ["fanale", "faro", "fiaccola", "illuminazione","lampada", "lume", "luminaria", "lucerna", "fanalino", "segnale luminoso", "indicatore"],
                "gloss": "per estensione"        
            }
        ]),
    ]
)
def test_parse_synonyms(word, expected_synsets):
    with open(os.path.join(resource_dir_path, f"{word}.txt"), "r", encoding="utf-8") as file:
        text = file.read()
        
    result = parse_itwiktionary_text(word, text)
    
    assert len(result[NodeType.SINONIMI.english_translation]) > 0, "No sinonimi sections found"
    for expected_synset in expected_synsets:
        print(f"Checking synset: gloss: {expected_synset['gloss']}, words: {sorted(expected_synset['words'])}")
        assert any(sorted(actual_synset["words"]) == sorted(expected_synset["words"]) and actual_synset["gloss"] == expected_synset["gloss"] for actual_synset in result[NodeType.SINONIMI.english_translation]), (
            f"Mismatch in section for '{word}'"
        )