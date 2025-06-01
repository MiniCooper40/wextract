import pytest
from src.wiktionary_parser import NodeType, parse_itwiktionary_text
import os

file_dir_path = os.path.dirname(os.path.abspath(__file__))
resource_dir_path = os.path.join(file_dir_path, "resources")

@pytest.mark.parametrize("title, expected_verbs", [
    ("passare", [
        {
            "type": "intransitivo",
            "definition": {
  "level_one": [
    "attraversare un luogo",
    "cambiare sede",
    "trascorrere (il tempo)",
    "promuovere, approvare",
    "superare un esame oppure \"uscire promossi\" e quindi accedere ad un livello scolastico successivo",     
    "dare, porgere qualcosa",
    "giungere a qualcosa di nuovo, migliore o ad una nuova situazione",
    "cambiare stato o condizione"
  ],
  "level_two": [
    [
      "passare per la strada"
    ],
    [
      "vuoi passare in soggiorno?"
    ],
    [
      "col passare degli anni le ossa si mineralizzano, cioè si arricchiscono di sali di calcio",
      "passare le vacanze in montagna"
    ],
    [
      "la proposta deve passare"
    ],
    [
      "mio figlio sta per passare in quinta elementare"
    ],
    [
      "mi potresti  passare del pane?"
    ],
    [
      "passare ad un livello più difficile",
      "siamo passati ai gadget"
    ],
    [
      "è passato dallo stato liquido allo stato gassoso"
    ]
  ],
  "level_three": [
    [],
    [],
    [],
    [],
    [],
    [],
    [],
    []
  ]
}
        },
        {
            "type": "transitivo",
            "definition": {
  "level_one": [
    "ridurre un cibo in poltiglia con un apposito utensile da cucina",
    "oltrepassare, attraversare qualcosa"
  ],
  "level_two": [
    [
      "passare la verdura"
    ],
    [
      "passare il confine"
    ]
  ],
  "level_three": [
    [],
    []
  ]
}
        }
        ]),
])
def test_parse_wiktionary_verb_infinitive(title, expected_verbs):
    with open(os.path.join(resource_dir_path, f"{title}.txt"), "r", encoding="utf-8") as file:
        text = file.read()
    result = parse_itwiktionary_text(title, text)
    
    actual_verbs = result[NodeType.VERBO.english_translation]
    assert len(actual_verbs) == 2, "Expected two verb sections, one for intransitive and one for transitive verbs."
    for verb in actual_verbs:
        verb_type = verb["type"]
        assert any(verb_type == expected_verb["type"] for expected_verb in expected_verbs), (
            f"Unexpected verb type '{verb_type}' found in the result for '{title}'."
        )
        expected_verb = [v for v in expected_verbs if v["type"] == verb_type][0]
        for level in expected_verb["definition"]:
            assert sorted(verb["definition"][level]) == sorted(expected_verb["definition"][level]), (
                f"Mismatch in verb definition for type '{verb_type}' in '{title}':\n"
                f"Expected: {expected_verb['definition']}\n"
                f"Got:      {verb['definition']}"
            )
