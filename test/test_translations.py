import pytest
from src.wiktionary_parser import NodeType, parse_itwiktionary_text
import os

file_dir_path = os.path.dirname(os.path.abspath(__file__))
resource_dir_path = os.path.join(file_dir_path, "resources")

@pytest.mark.parametrize("title, expected_translations", [
    ("verde", 
        {
            "en": [
                "vert (se usato per i cittadini comuni)",
                "emerald (se usato per i nobili)",
                "venus (se usato per i principi e i sovrani)",
                "green"
            ]
        }
    ),
])
def test_parse_wiktionary_translations(title, expected_translations):
    with open(os.path.join(resource_dir_path, f"{title}.txt"), "r", encoding="utf-8") as file:
        text = file.read()
    result = parse_itwiktionary_text(title, text)
    translations = result.get(NodeType.TRADUZIONE.english_translation, {})
    assert len(translations) == 1, "No traduzione section found"
    translations = translations[0]
    # Flatten all English translations from all translation sections
    for lang, cur_expected_translations in expected_translations.items():
        current_translations = set()
        for l, translation_senses in translations.items():
            if lang == l:
                for translation_sense in translation_senses:
                    current_translations.update(translation_sense.get("translations", []))
        
        assert current_translations == set(cur_expected_translations), f"Missing expected translation: {expected_translations}"
