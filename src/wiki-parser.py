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

def processed_page_element(elem, namespace):
    title_elem = elem.find(f"{{{namespace}}}title")
    if title_elem is not None:
        title = title_elem.text
    
    if title is None:
        return None
    
    # Check if title starts with two capitalized words
    tokens = title.split(" ")
    if (len(tokens) > 1 and all(t[0].isupper() for t in tokens[:1])) or re.search(r'\d', title):
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
                pass
        if id is not None and id % 10000 == 0:
            print(f"Processed page {id}")

        extracted = {
            "form": title,
            "id": id,
            "base_url": urllib.parse.quote(base_url.replace("Pagina_principale", title), safe=':/') if base_url else None,
        }
    
    return extracted
           
def process_wiki(wiki_dump_path, output_folder_path):
    global base_url
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

        # max_pages = 4000000
        num_pages = 0

        queue = Queue(maxsize=1000)

        file_locks = {}

        def get_file_lock(path):
            if path not in file_locks:
                file_locks[path] = threading.Lock()
            return file_locks[path]

        def worker():
            while True:
                item = queue.get()
                if item is None:
                    break
                
                elem, namespace, output_path = item
                # try:
                processed_page = processed_page_element(elem, namespace)
                lock = get_file_lock(output_path)
                if processed_page is not None:
                    with lock:
                        with open(output_path, 'a', encoding='utf-8') as output_file:
                            output_file.write(json.dumps(processed_page, ensure_ascii=False) + "\n")
                                
                # except Exception as e:
                #     print(f"Error processing page: {e}")
                #     # print(e)

                
                elem.clear()
                while elem.getprevious() is not None:
                    del elem.getparent()[0]
                

                queue.task_done()

        num_worker_threads = multiprocessing.cpu_count()
        print(f"Using {num_worker_threads} worker threads")
        threads = []
        for i in range(num_worker_threads):
            t = threading.Thread(target=worker)
            t.start()
            threads.append(t)

        for _, elem in context:
            pass

        print("Queued all tasks")
        # Block until all tasks are done
        queue.join()

        print("All tasks completed")
        # Stop workers
        for i in range(num_worker_threads):
            queue.put(None)
        for t in threads:
            t.join()