
import argparse
import os
from wiktionary_parser import process_itwiktionary
import json
from glob import glob
from sortedcontainers import SortedDict
import pickle
            

def save_sorted_dict(output_folder):
    all_objects = SortedDict()
    subfolders = [os.path.join(output_folder, d) for d in os.listdir(output_folder)
                    if os.path.isdir(os.path.join(output_folder, d)) and d.startswith("folder-")]
    for subfolder in subfolders:
        jsonl_files = glob(os.path.join(subfolder, "*.jsonl"))
        for jsonl_file in jsonl_files:
            with open(jsonl_file, "r", encoding="utf-8") as f:
                for line in f:
                    obj = json.loads(line)
                    key = obj.get("form")
                    if key is not None:
                        all_objects[key] = obj
    with open(os.path.join(output_folder, "wiktionary.pkl"), "wb") as f:
        pickle.dump(all_objects, f)

def main():
    parser = argparse.ArgumentParser(description="Process a Wikipedia XML dump.")
    
    parser.add_argument('--input', required=True, help='Path to the input XML file')
    parser.add_argument('--wiktionary', action='store_true', default=False, help='Process as Wiktionary dump')
    parser.add_argument('--no-parse', action='store_true', default=False, help='Skip parsing and only extract sorted dict')
    parser.add_argument('--output', required=True, help='Output folder path')
    parser.add_argument('--max-pages', type=int, nargs='?', default=float('inf'), help='Maximum number of pages to process (default: inf for all pages)')
    parser.add_argument('--log-stats', action='store_true', default=False, help='Log statistics')
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument('--sorted-dict', action='store_true', default=False, help='Save sorted dictionary to output folder')
    if parser.parse_args().debug:
        os.environ["DEBUG"] = "True"
    args = parser.parse_args()
    
    if args.wiktionary:
        if not args.no_parse:
            process_itwiktionary(args.input, args.output, max_pages=args.max_pages, log_stats=args.log_stats)
        if args.sorted_dict:
            save_sorted_dict(args.output)
        
if __name__ == "__main__":
    main()