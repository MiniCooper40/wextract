import sys
import pickle
from pprint import pprint

def main():
    if len(sys.argv) != 3:
        print("Usage: python query.py <path_to_pickle> <word>")
        sys.exit(1)

    pickle_path = sys.argv[1]
    word = sys.argv[2]

    # Load the SortedDict from the pickle file
    with open(pickle_path, 'rb') as f:
        sorted_dict = pickle.load(f)

    # Find and pretty print the item with key=word
    if word in sorted_dict:
        pprint(sorted_dict[word])
    else:
        print(f"Key '{word}' not found in the SortedDict.")

if __name__ == "__main__":
    main()