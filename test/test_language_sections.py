import pytest
from src.wiktionary_parser import itwikitionary_text_to_wikicode, parse_itwiktionary_language_sections, parse_itwiktionary_text
import os

file_dir_path = os.path.dirname(os.path.abspath(__file__))
resource_dir_path = os.path.join(file_dir_path, "resources")

@pytest.mark.parametrize(
    "title,languages",
    [
        ("verde", ["es", "it", "pt"]),
    ]
)
def test_parse_languages(title, languages):
    with open(os.path.join(resource_dir_path, f"{title}.txt"), "r", encoding="utf-8") as file:
        text = file.read()
        
    wikicode = itwikitionary_text_to_wikicode(text)
    language_sections = parse_itwiktionary_language_sections(wikicode)
    
    found_languages = [section["title"] for section in language_sections]
    
    assert len(found_languages) > 0, f"No language sections found for '{title}'"
    assert sorted(languages) == sorted(found_languages), f"Languages do not match for '{title}'. Expected: {sorted(languages)}, Found: {sorted(found_languages)}"
