from collections import Counter, defaultdict, deque
import json
import time
from lxml import etree
import mwparserfromhell
import re
import nltk
import threading
from queue import Queue
import os
import multiprocessing
import urllib.parse
import nltk
from enum import Enum, auto
import numpy as np

nltk.download('punkt', quiet=True)

all_found_form_lines = Counter()

class NoItalianSection(Exception):
    """Custom exception raised when no Italian section is found in the Wiktionary text."""
    def __init__(self, title):
        super().__init__(f"No Italian section found for the title: {title}")

class NodeType(Enum):
    SOSTANTIVO = auto()
    AGGETTIVO = auto()
    AVVERBIO = auto()
    SOSTANTIVO_FLESSA = auto()
    AGGETTIVO_FLESSA = auto()
    SINONIMI = auto()
    ANTONIMI = auto()
    DERIVATIVE = auto()
    TRADUZIONE = auto()
    PROVERBIO = auto()
    VERBO = auto()

    @property
    def english_translation(self):
        translations = {
            NodeType.SOSTANTIVO: "noun",
            NodeType.AGGETTIVO: "adjective",
            NodeType.AVVERBIO: "adverb",
            NodeType.SOSTANTIVO_FLESSA: "inflected_noun",
            NodeType.AGGETTIVO_FLESSA: "inflected_adjective",
            NodeType.SINONIMI: "synonyms",
            NodeType.ANTONIMI: "antonyms",
            NodeType.DERIVATIVE: "derivative",
            NodeType.TRADUZIONE: "translation",
            NodeType.PROVERBIO: "proverb",
            NodeType.VERBO: "verb",
        }
        return translations.get(self, "unknown")

    def __str__(self):
        return self.name.lower()

    def __repr__(self):
        return f'"{self.name.lower()}"'

# Filepath to your large XML file
output_folder_template = "folder-TEMP"
output_filename_tamplate = "wiki-TEMP.jsonl"

base_url = ""

def parse_itwiktionary_it_section(wikicode):
    wikicode_text = str(wikicode).strip()
    section_matches = re.findall(r"{{\s*?-(.*?)-\s*?\|?(.*?)}}([\w\W]*?)(?={{\s*-|\Z)", wikicode_text, re.DOTALL)
    sections = []
    
    for match in section_matches:
        section_name = match[0].strip()
        section_params = match[1].strip().split("|")
        section_params = [param.strip() for param in section_params if param.strip()]
        section_content = match[2].strip()
        
        node_type = None
        
        if os.environ.get("DEBUG") == "True":
            print(f"Found section: {section_name}, params: {section_params}")
        
        if section_name == "sost":
            node_type = NodeType.SOSTANTIVO
        elif section_name == "sin":
            node_type = NodeType.SINONIMI
        elif section_name == "ant":
            node_type = NodeType.ANTONIMI
        elif section_name == "der":
            node_type = NodeType.DERIVATIVE
        elif section_name == "agg form":
            node_type = NodeType.AGGETTIVO_FLESSA
        elif section_name == "agg":
            node_type = NodeType.AGGETTIVO
        elif section_name == "avv":
            node_type = NodeType.AVVERBIO
        elif section_name == "verb form":
            node_type = NodeType.SOSTANTIVO_FLESSA
        elif section_name == "trad":
            node_type = NodeType.TRADUZIONE
        elif section_name == "prov":
            node_type = NodeType.PROVERBIO
        elif section_name == "verb":
            node_type = NodeType.VERBO
            
        sections.append({
            "node_type": node_type,
            "params": section_params,
            "content": mwparserfromhell.parse(section_content),
        })
    
    return sections

def parse_itwiktionary_language_sections(wikicode):
    wikicode_text = str(wikicode).strip()
    section_matches = re.findall(r"(?:^==\s{0,1}{{-(.*?)-}}\s{0,1}==)([\w\W]*?)(?=(?:\s*?==\s*{{|\Z))", wikicode_text, re.MULTILINE | re.DOTALL)
    
    if os.environ.get("DEBUG") == "True":
        print(f"Found language sections: {[match[0].strip() for match in section_matches]}")
    
    sections = [{"title": match[0].strip(), "content": mwparserfromhell.parse(match[1].strip())} for match in section_matches]
    
    return sections

def parse_itwiktionary_form_line(word:str, form_line: str):
    global all_found_form_lines
    
    form_line_node = mwparserfromhell.parse(form_line)    
    
    if os.environ.get("DEBUG") == "True":
        print(f"Form line for word: {word}. Got node: {form_line_node}")
    
    forms = {
        "ms": None,
        "fs": None,
        "mp": None,
        "fp": None,
        "self": None,
        "gender_invariant": False,
        "number_invariant": False
    }
    
    for template in form_line_node.filter_templates():
        if template.name.matches("Tabs"):
            if len(template.params) == 4:
                forms["ms"] = str(template.params[0]).strip()
                forms["mp"] = str(template.params[1]).strip()
                forms["fs"] = str(template.params[2]).strip()
                forms["fp"] = str(template.params[3]).strip()
            else:
                raise ValueError(f"Unexpected number of parameters in Tab template. Got \n\t[{template.params}]\n, expected 4.")
        elif template.name.matches("Linkp"):
            plural_form = str(template.params[0]).strip()
            forms["mp"] = plural_form
            forms["fp"] = plural_form
        elif template.name.matches("Non numerabile"):
            forms["number_invariant"] = True
        form_line_node.remove(template)
    
    form_line_text = form_line_node.strip_code().strip()
    if os.environ.get("DEBUG") == "True":
        print(f"Form line text for word: {word}. Got node: {form_line_text}")
    form_line_text = re.sub(r'\(.*?\)', '', form_line_text).strip()
    form_line_text = form_line_text.replace("'", "").strip()
    form_line_text = form_line_text.replace("sinf", "sing")
    form_line_text = form_line_text.replace("maschile", "m").replace("femminile", "f")
    form_line_text = form_line_text.replace("plurale", "pl").replace("singolare", "sing")
    form_line_text = form_line_text.replace("plur", "pl").replace("sing", "sing")
    form_line_text = form_line_text.replace(",", "").replace(";", "").replace(".", "").strip()
    form_line_text = re.sub(r'\s{2,}', ' ', form_line_text).strip()
    
    if os.environ.get("DEBUG") == "True":
        print(f"After additional processing form line text for word: {word}. Got node: {form_line_text}")
    
    if form_line_text == "":
        print(f"Empty form line for word: {word}. Got node: {form_line_node}")
    
    all_found_form_lines.update({form_line_text: 1})
    
    if form_line_text in {"m sing", "m", "sing m"}:
        forms["self"] = "ms"
        if forms["ms"] is None:
            forms["ms"] = word
            forms["fp"] = None
    elif form_line_text in {"f sing", "f", "sing f"}:
        forms["self"] = "fs"
        if forms["fs"] is None:
            forms["fs"] = word
            forms["mp"] = None
    elif form_line_text in {"m plur", "m pl", "plur m"}:
        forms["self"] = "mp"
        if forms["mp"] is None:
            forms["mp"] = word
    elif form_line_text in {"f plur", "f pl", "plur f"}:
        forms["self"] = "fp"
        if forms["fp"] is None:
            forms["fp"] = word
    elif form_line_text in {"m e f sing", "sing m e f"}:
        forms["self"] = "mfs"
        if forms["ms"] is None:
            forms["ms"] = word
        if forms["fs"] is None:
            forms["fs"] = word
    elif form_line_text == "m solo sing":
        forms["self"] = "ms"
        if forms["ms"] is None:
            forms["ms"] = word
    elif form_line_text == "f solo sing":
        forms["self"] = "fs"
        if forms["fs"] is None:
            forms["fs"] = word
    elif form_line_text == "m inv":
        forms["self"] = "m"
        forms["ms"] = word
        forms["mp"] = word
        forms["number_invariant"] = True
    elif form_line_text == "f inv":
        forms["self"] = "f"
        forms["fs"] = word
        forms["fp"] = word
        forms["number_invariant"] = True
    elif form_line_text == "inv sing":
        forms["gender_invariant"] = True
        forms["fs"] = word
        forms["ms"] = word
        forms["self"] = "mfs"
    
    return forms
    
def remove_unused_wiki_content(wikicode):
    sections_to_remove = []
    
    for node in wikicode.filter_wikilinks():
        if node.title.strip().lower().startswith(("file", "immagine", "categoria")):
            sections_to_remove.append(node)
             
    for section in sections_to_remove:
        wikicode.remove(section)
        
    return wikicode 

def parse_definitions(text: str, word: str):
    definitions = re.findall(r'(#[^*].*?)(?=\n#[^*]|\Z)', text, re.DOTALL)
    if os.environ.get("DEBUG") == "True":
        print(f"Found definitions: {len(definitions)}")
    level_one = []
    level_two = []
    level_three = []
    
    for definition in definitions:
        definition = definition.strip()
        lines = definition.split("\n")
        
        level_two_cur = []
        level_three_cur = []
        level_three_cur_indent = []
        
        for line in lines:
            line_node = mwparserfromhell.parse(line)
            for template in line_node.filter_templates():
                if template.name.matches("Pn"):
                    line_node.replace(template, word)
                else:
                    continue
            cleaned_line = line_node.strip_code().strip()
            if re.match(r"^#\*\*[^*]", line, re.DOTALL):
                level_three_cur_indent.append(cleaned_line)
            elif re.match(r"^#\*[^*]", line, re.DOTALL):
                if len(level_two) > 0:
                    level_three_cur_indent = []
                level_two_cur.append(cleaned_line)
            elif re.match(r"^#[^*]", line, re.DOTALL):
                level_two_cur = []
                level_one.append(cleaned_line)

        level_three.append(level_three_cur)
        level_two.append(level_two_cur)
        
    return {
        "level_one": level_one,
        "level_two": level_two,
        "level_three": level_three,
    }

def parse_itwiktionary_avverbio_section(avverbio_section, title):
    avverbio_text = str(avverbio_section).strip()
   
    if os.environ.get("DEBUG") == "True":
        print(f"Parsing avverbio section for word: {title}. Got node: {avverbio_text}")
   
    return {
        "definitions": parse_definitions(avverbio_text, title)
    }
        

def parse_itwiktionary_sostantivo_section(sostantivo_section, title):
    
    if os.environ.get("DEBUG") == "True":
        print(f"Parsing sostantivo section for word: {title}. Got node: {sostantivo_section}")
    
    for template in sostantivo_section.filter_templates():
        if template.name.matches("Tabs"):
            param_mapping = {i+1: str(param).replace("\n", "") for i, param in enumerate(template.params)}
            for key, value in param_mapping.items():
                template.remove(key)
                template.add(key, value, showkey=False)
        if template.name.matches("W"):
            sostantivo_section.remove(template)
                
    sostantivo_text = str(sostantivo_section).strip()
    
    form_line = ""
    if sostantivo_text.lstrip().startswith("{{Pn"):
        form_line = sostantivo_text.lstrip().split("\n#")[0].replace("\n", "")
    elif re.match(r"^'''.*?'''", sostantivo_text):
        form_line = sostantivo_text.lstrip().split("\n#")[0].replace("\n", "")
        form_line = re.sub(r"'''(.*?)'''", "", form_line).strip()

    if os.environ.get("DEBUG") == "True":
        print(f"Form line for word: {title}. Got node: {form_line}")
    
    definitions = parse_definitions(str(sostantivo_section).strip(), title)
        
    return {
        "definitions": definitions,
        "forms": parse_itwiktionary_form_line(title, form_line),
        "form_line": mwparserfromhell.parse(form_line).strip_code().strip() if form_line else None,
    }

def parse_itwiktionary_sinonimi_like_section(sinonimi_section, title):
    synsets = []
    
    lines = str(sinonimi_section).strip().split("\n")
    for line in lines:
        line_node = mwparserfromhell.parse(line)
        line = line_node.strip_code().strip() 
               
        gloss = re.findall(r'\((.*?)\)', line)
        
        for template in line_node.filter_templates():
            if template.name.matches("Est"):
                gloss = "per estensione"
            elif template.name.matches("Term"):
                gloss = template.params[0].strip()
            elif template.name.matches("Fig"):
                gloss = "senso figurato"
        
        line = line[line.find(")")+1 if line.startswith("(") else 0:].strip()
        words = [word.strip() for word in line.split(",") if len(word.strip()) > 0]
        
        synsets.append({
            "words": sorted(list(set(words))),
            "gloss": gloss[0] if isinstance(gloss, list) and len(gloss) else gloss or None,
        })
    
    return synsets

def parse_itwiktionary_translation_section(traduzione_section, title):
    found_translations = defaultdict(list)
    translation_sections = re.findall(r"{{Trad1(?:\|(.*?)){0,1}}}([\w\W]*?){{Trad2}}", str(traduzione_section), re.DOTALL)
    for translation_section in translation_sections:
        translation_node = mwparserfromhell.parse(translation_section[1])
        for wikilink in translation_node.filter_wikilinks():
            translation_node.replace(wikilink, wikilink.text or wikilink.title)
        translations = re.findall(r":\*{{(.*?)}}:([\w\W]*?)\n", translation_section[1], re.DOTALL)
        sense = translation_section[0].strip()
        for match in translations:
            lang = match[0].strip()
            translations_text = match[1].strip()
            if lang != "en":
                continue
            if os.environ.get("DEBUG") == "True":
                print(f"Found translation for language: {lang}, text: {translations_text}")
            translations_node = mwparserfromhell.parse(translations_text)
            translations_text = translations_node.strip_code().strip()
            found_translations[lang].append({
                "sense": sense,
                "translations": [translation.strip() for translation in translations_text.split(",")] if translations_text else []
            })
            
    return found_translations

def parse_itwiktionary_verbo_section(verbo_section, title):
    if os.environ.get("DEBUG") == "True":
        print(f"Parsing verbo section for word: {title}. Got node: {verbo_section}")
    verb_subsections = re.findall(r"\{\{([Tt]ransitivo|[Ii]ntransitivo|[Rr]eflesivo)\|.*?\}\}([\w\W]*?)(?=\{\{(?:[Tt]ransitivo|[Ii]ntransitivo|[Rr]eflesivo)|\Z)", str(verbo_section), re.DOTALL | re.MULTILINE)
    sections = []
    if os.environ.get("DEBUG") == "True":
        print(f"Found verb subsections: {len(verb_subsections)}")
    for verb_subsection in verb_subsections:
        verb_type = verb_subsection[0].strip().lower()
        verb_content = verb_subsection[1].strip()
        
        if os.environ.get("DEBUG") == "True":
            print(f"Found verb subsection: {verb_type}, content: {verb_content}")
        
        if verb_type in {"transitivo", "intransitivo", "reflesivo"}:
            sections.append({
                "type": verb_type,
                "definition": parse_definitions(verb_content, title),
            })
    
    return sections

node_type_parser: dict[NodeType, callable] = {
    NodeType.SOSTANTIVO: parse_itwiktionary_sostantivo_section,
    NodeType.AGGETTIVO: parse_itwiktionary_sostantivo_section,
    NodeType.AVVERBIO: parse_itwiktionary_avverbio_section,
    NodeType.SOSTANTIVO_FLESSA: None,
    NodeType.AGGETTIVO_FLESSA: None,
    NodeType.SINONIMI: parse_itwiktionary_sinonimi_like_section,
    NodeType.ANTONIMI: parse_itwiktionary_sinonimi_like_section,
    NodeType.DERIVATIVE: parse_itwiktionary_sinonimi_like_section,
    NodeType.TRADUZIONE: parse_itwiktionary_translation_section,
    NodeType.PROVERBIO: parse_itwiktionary_avverbio_section,
    NodeType.VERBO: parse_itwiktionary_verbo_section,
}

class ThreadSafeList:
    def __init__(self):
        self.list = deque()
        self.lock = multiprocessing.Lock()

    def append(self, item):
        with self.lock:
            self.list.append(item)

    def pop(self):
        with self.lock:
            return self.list.popleft() if self.list else None

    def __len__(self):
        with self.lock:
            return len(self.list)
        
    def __list__(self):
        with self.lock:
            return list(self.list)
        
    def as_numpy(self):
        with self.lock:
            return np.array(self.list)
        
def itwikitionary_text_to_wikicode(text):
    wikicode = mwparserfromhell.parse(text)
    wikicode = remove_unused_wiki_content(wikicode)
    return wikicode

def parse_itwiktionary_text(title, text):
    wikicode = itwikitionary_text_to_wikicode(text)
    language_sections = parse_itwiktionary_language_sections(wikicode)
    if os.environ.get("DEBUG") == "True":
        language_section_counts = Counter([section["title"] for section in language_sections])
        print(f"Language sections found: {language_section_counts}")
    
    it_section = next((section["content"] for section in language_sections if "it" in section["title"].lower()), None)
    if it_section is None:
        raise NoItalianSection(f"\"{title}\" has no Italian section.")
    
    parsed_it_sections = parse_itwiktionary_it_section(it_section)
    if os.environ.get("DEBUG") == "True":
        it_section_counts = Counter([section["node_type"] for section in parsed_it_sections])
        print(f"Italain sections found: {it_section_counts}")
    
    page_content = defaultdict(list)
    
    for node_type, callable in node_type_parser.items():
        if node_type is None or callable is None:
            continue
        for parsed_section in parsed_it_sections:
            if parsed_section["node_type"] == node_type:
                parsed_result = callable(parsed_section["content"], title)
                if isinstance(parsed_result, list):
                    page_content[node_type].extend(parsed_result)
                else:
                    page_content[node_type].append(parsed_result)
     
    return {node_type.english_translation: page_content[node_type] for node_type in NodeType if node_type in page_content}

def processed_page_element(elem, namespace):
    title_elem = elem.find(f"{{{namespace}}}title")
    if title_elem is not None:
        title = title_elem.text
    
    if title is None:
        return None
    
    id_elem = elem.find(f"{{{namespace}}}id")
    if id_elem is not None:
        id =  int(id_elem.text) if int(id_elem.text) else -1
    
    revision_elem = elem.find(f"{{{namespace}}}revision")
    
    if revision_elem is not None:
        text_elem = revision_elem.find(f"{{{namespace}}}text")
        if text_elem is not None:
            article_text = text_elem.text
            if article_text is not None:
               parsed_article = parse_itwiktionary_text(title, article_text)
                
        if id is not None and id % 10000 == 0:
            print(f"Processed page {id}")

        extracted = {
            **parsed_article,
            "form": title,
            "id": id,
            "base_url": urllib.parse.quote(base_url.replace("Pagina_principale", title), safe=':/') if base_url else None,
        }
    
    return extracted
            
def process_itwiktionary(wiki_dump_path, output_folder_path, *, log_stats=False, max_pages=float('inf')):
    global base_url

    process_start_time = time.time() if log_stats else None
    runtimes = ThreadSafeList()
    
    print(f"Processing Wiktionary dump: {wiki_dump_path}")
    print(f"Maximum pages to process: {max_pages}")
    
    # Open the file and parse it incrementally
    with open(wiki_dump_path, 'rb') as file:
        # Extract the namespace from the root element
        for event, elem in etree.iterparse(file, events=("start",)):
            if elem.tag.startswith("{"):
                namespace = elem.tag.split("}")[0].strip("{")
                break

        # Reset the file pointer to the beginning
        file.seek(0)
        
        ns_map = {}
        
        # Find the first <siteinfo> element in the XML file
        for event, elem in etree.iterparse(file, events=("end",), tag=f"{{{namespace}}}siteinfo"):
            base_elem = elem.find(f"{{{namespace}}}base")
            base_url = base_elem.text if base_elem is not None else None
            namespaces_elem = elem.find(f"{{{namespace}}}namespaces")
            for ns_elem in namespaces_elem:
                ns_id = ns_elem.attrib.get("key")
                ns_name = ns_elem.text
                if ns_id and ns_name:
                    ns_map[ns_id] = ns_name
            break

        file.seek(0)
        
        # Use lxml's iterparse to process the file incrementally with the extracted namespace
        context = etree.iterparse(file, events=("end",), tag=f"{{{namespace}}}page")

        num_pages = 0

        try:
            queue = Queue(maxsize=1000)

            file_locks = {}

            def get_file_lock(path):
                if path not in file_locks:
                    file_locks[path] = threading.Lock()
                return file_locks[path]

            def worker():
                while True:
                    # print("Waiting for item in queue...")
                    item = queue.get()
                    # print("Got item from queue")
                    start_time = time.time() if log_stats else None
                    if item is None:
                        break
                    
                    elem, namespace, output_path = item
                    try:
                        processed_page = processed_page_element(elem, namespace)
                        lock = get_file_lock(output_path)
                        if processed_page is not None:
                            # print("Waiting for lock on:", output_path)
                            with lock:
                                with open(output_path, 'a', encoding='utf-8') as output_file:
                                    output_file.write(json.dumps(processed_page, ensure_ascii=False, default=lambda o: o.name if isinstance(o, NodeType) else o, sort_keys=True) + "\n")
                                    end_time = time.time() if log_stats else None
                                    if log_stats and end_time is not None:
                                        runtimes.append(end_time - start_time)
                            # print(f"Released lock on: {output_path}")
                    except NoItalianSection as e:
                        pass                    
                    except Exception as e:
                        print(e)
                    finally:
                        queue.task_done()
                        elem.clear()
                        while elem.getprevious() is not None:
                            del elem.getparent()[0]

            num_worker_threads = multiprocessing.cpu_count()
            print(f"Using {num_worker_threads} worker threads")
            threads = []
            for i in range(num_worker_threads):
                t = threading.Thread(target=worker)
                t.start()
                threads.append(t)

            for _, elem in context:
                output_folder_name = output_folder_template.replace("TEMP", str(num_pages // 5000000))
                output_filename = output_filename_tamplate.replace("TEMP", str(num_pages // 100000))
                output_path = os.path.join(output_folder_path, output_folder_name, output_filename)
                
                if not os.path.exists(os.path.dirname(output_path)):
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                if not os.path.exists(output_path):
                    with open(output_path, 'w', encoding='utf-8') as f:
                        pass
                    
                queue.put((elem, namespace, output_path))
                # print(f"Queued task for page {num_pages} to {output_path}")
                num_pages += 1
                if num_pages >= max_pages:
                    break

            # print("Queued all tasks:", num_pages)
            # Block until all tasks are done
            queue.join()

            # print("All tasks completed")
            # Stop workers
            for i in range(num_worker_threads):
                queue.put(None)
            for t in threads:
                t.join()
        except Exception as e:
            print(f"An error occurred: {e}")
        
    if log_stats:
        print("Statistics:")
        print(f"Total pages processed: {num_pages}")
        print(f"Total form lines found: {len(all_found_form_lines)}")
        for form_line, count in all_found_form_lines.items():
            print(f"\"{form_line}\": {count}")
        if runtimes:
            runtimes_array = runtimes.as_numpy()
            print("Runtime Statistics:")
            print(f"Threads used: {num_worker_threads}")
            print(f"Total runtime: {time.time() - process_start_time:.4f} seconds")
            print(f"Effective runtime: {np.sum(runtimes_array):.4f} seconds")
            print(f"Mean: {np.mean(runtimes_array):.4f} seconds")
            print(f"Median: {np.median(runtimes_array):.4f} seconds")
            print(f"Standard Deviation: {np.std(runtimes_array):.4f} seconds")
            print(f"Min: {np.min(runtimes_array):.4f} seconds")
            print(f"Max: {np.max(runtimes_array):.4f} seconds")