import os
import re

def get_codebase_files(directory, file_extensions=['.py', '.md']):
    """
    Traverses a directory and returns a list of file paths with specified extensions.

    Args:
        directory (str): The root directory to traverse.
        file_extensions (list): A list of file extensions to include.

    Returns:
        list: A list of absolute file paths.
    """
    filepaths = []
    for root, _, files in os.walk(directory):
        for file in files:
            if any(file.endswith(ext) for ext in file_extensions):
                filepaths.append(os.path.join(root, file))
    return filepaths

def parse_python_file(filepath, content):
    """
    Parses a Python file to extract functions and classes as document chunks.

    Args:
        filepath (str): The path to the file.
        content (str): The content of the file.

    Returns:
        list: A list of document dictionaries.
    """
    documents = []
    # Regex to find function or class definitions, including docstrings and comments
    # This regex is a basic attempt and might need refinement for complex cases
    pattern = re.compile(r'^(def|class)\s+([\w_]+)\s*\(.*?\):.*?(\n(?:\s{4}.*|\s*#.*|\s*"""[\s\S]*?"""|\s*\'\'\'[\s\S]*?\'\'\'))*', re.DOTALL | re.MULTILINE)

    for match in pattern.finditer(content):
        definition_type = match.group(1)
        name = match.group(2)
        snippet = match.group(0).strip()
        start_line = content[:match.start()].count('\n') + 1
        end_line = start_line + snippet.count('\n')

        documents.append({
            'text': snippet,
            'metadata': {
                'file_path': filepath,
                'type': definition_type,
                'name': name,
                'start_line': start_line,
                'end_line': end_line,
            }
        })

    # If no functions or classes found, treat the whole file as one document
    if not documents and content.strip():
         documents.append({
            'text': content,
            'metadata': {
                'file_path': filepath,
                'type': 'file',
                'start_line': 1,
                'end_line': content.count('\n') + 1,
            }
        })


    return documents

def parse_markdown_file(filepath, content):
    """
    Parses a Markdown file to extract sections based on headings as document chunks.

    Args:
        filepath (str): The path to the file.
        content (str): The content of the file.

    Returns:
        list: A list of document dictionaries.
    """
    documents = []
    # Split by headings (h1 to h6)
    sections = re.split(r'^(#+\s+.*)$', content, flags=re.MULTILINE)

    current_heading = "File Content"
    current_content = ""
    start_line = 1

    for i, section in enumerate(sections):
        if i == 0 and not section.strip():
            continue # Skip empty content before the first heading

        if section.startswith('#'):
            if current_content.strip():
                 documents.append({
                    'text': f"{current_heading}\n{current_content.strip()}",
                    'metadata': {
                        'file_path': filepath,
                        'type': 'markdown_section',
                        'heading': current_heading.strip('# ').strip(),
                        'start_line': start_line,
                        'end_line': start_line + current_content.count('\n'),
                    }
                })
            current_heading = section.strip()
            current_content = ""
            start_line = content.find(section) + 1 # Approximate start line
            start_line = content[:start_line-1].count('\n') + 1 # More accurate start line
        else:
            current_content += section
            if i == len(sections) - 1 and current_content.strip():
                 documents.append({
                    'text': f"{current_heading}\n{current_content.strip()}",
                    'metadata': {
                        'file_path': filepath,
                        'type': 'markdown_section',
                        'heading': current_heading.strip('# ').strip(),
                        'start_line': start_line,
                        'end_line': start_line + current_content.count('\n'),
                    }
                })


    # If no sections found (e.g., no headings), treat the whole file as one document
    if not documents and content.strip():
         documents.append({
            'text': content,
            'metadata': {
                'file_path': filepath,
                'type': 'file',
                'start_line': 1,
                'end_line': content.count('\n') + 1,
            }
        })

    return documents


def parse_file(filepath):
    """
    Reads a file and returns a list of document chunks with metadata based on file type.

    Args:
        filepath (str): The path to the file.

    Returns:
        list: A list of document dictionaries, or an empty list if file cannot be read or parsed.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        if filepath.endswith('.py'):
            return parse_python_file(filepath, content)
        elif filepath.endswith('.md'):
            return parse_markdown_file(filepath, content)
        else:
            # For other file types, return the whole file as a single document
             return [{
                'text': content,
                'metadata': {
                    'file_path': filepath,
                    'type': 'file',
                    'start_line': 1,
                    'end_line': content.count('\n') + 1,
                }
            }]
    except Exception as e:
        print(f"Error reading or parsing file {filepath}: {e}")
        return []

def load_codebase_artifacts(directories=['.']):
    """
    Loads codebase artifacts from specified directories.

    Args:
        directories (list): A list of directories to scan.

    Returns:
        list: A list of document dictionaries.
    """
    all_documents = []
    for directory in directories:
        print(f"Scanning directory: {directory}")
        filepaths = get_codebase_files(directory)
        print(f"Found {len(filepaths)} files in {directory}")
        for filepath in filepaths:
            documents = parse_file(filepath)
            all_documents.extend(documents) # Extend with the list of documents from parse_file
    return all_documents

if __name__ == '__main__':
    # Example Usage
    # Assuming this script is run from the root of the Pulse repository
    # Create dummy files for testing
    dummy_py_content = """
import os

def my_function(arg1):
    \"\"\"This is a docstring.\"\"\"
    # This is a comment
    print(arg1)

class MyClass:
    def __init__(self, value):
        self.value = value

    def my_method(self):
        # Another comment
        return self.value * 2
"""
    dummy_md_content = """
# Main Heading

This is the first paragraph.

## Section 1

Content of section 1.

### Sub-section 1.1

Content of sub-section 1.1.

## Section 2

Content of section 2.
"""
    os.makedirs('./temp_test_dir', exist_ok=True)
    with open('./temp_test_dir/dummy.py', 'w') as f:
        f.write(dummy_py_content)
    with open('./temp_test_dir/dummy.md', 'w') as f:
        f.write(dummy_md_content)
    with open('./temp_test_dir/dummy.txt', 'w') as f:
        f.write("This is a plain text file.")


    codebase_docs = load_codebase_artifacts(directories=['./temp_test_dir'])

    print(f"\nLoaded a total of {len(codebase_docs)} document chunks.")
    # Print some sample documents
    for i, doc in enumerate(codebase_docs):
        print(f"--- Document {i+1} ---")
        print(f"File Path: {doc['metadata']['file_path']}")
        print(f"Type: {doc['metadata'].get('type', 'N/A')}")
        if 'name' in doc['metadata']:
             print(f"Name: {doc['metadata']['name']}")
        if 'heading' in doc['metadata']:
             print(f"Heading: {doc['metadata']['heading']}")
        print(f"Lines: {doc['metadata'].get('start_line', 'N/A')}-{doc['metadata'].get('end_line', 'N/A')}")
        print(f"Text Snippet:\n{doc['text'][:500]}...") # Print first 500 characters
        print("-" * 20)

    # Clean up dummy files
    os.remove('./temp_test_dir/dummy.py')
    os.remove('./temp_test_dir/dummy.md')
    os.remove('./temp_test_dir/dummy.txt')
    os.rmdir('./temp_test_dir')