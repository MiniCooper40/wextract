import argparse
from wiktionary_parser import parse_itwiktionary_text
from pprint import pprint
import os

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", help="Path to the file")
    parser.add_argument("--name", help="Name of entity")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    if parser.parse_args().debug:
        os.environ["DEBUG"] = "True"
    args = parser.parse_args()
    
    with open(args.file, 'r', encoding='utf-8') as f:
        file_content = f.read()
        result = parse_itwiktionary_text(args.name, file_content)
        pprint(result)
    