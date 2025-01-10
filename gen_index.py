#!/usr/bin/env python3

import os
import datetime
import subprocess
from pathlib import Path

# -------------------------------
# Configuration Section
# -------------------------------

# Define the name of the CSS file
CSS_FILENAME = "style.css"

# Define the GitHub repository URL
GITHUB_REPO_URL = "https://github.com/sec-bit/mle-pcs/"

# Add this constant near the top of the file, with the other configurations
GOOGLE_ANALYTICS_ID = "G-JT3HKW7GRY"  # Replace XXXXXXXXXX with your actual Google Analytics ID

# HTML templates
HTML_TEMPLATE_START = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PDF Repository</title>
    <link rel="stylesheet" href="{css_filename}">
    <!-- Google Analytics -->
    <script async src="https://www.googletagmanager.com/gtag/js?id={google_analytics_id}"></script>
    <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){{dataLayer.push(arguments);}}
        gtag('js', new Date());
        gtag('config', '{google_analytics_id}');
    </script>
</head>
<body>
    <header>
        <h1>PDF Repository</h1>
        <p>Last updated: {build_time}</p>
        <!-- GitHub Repository Link -->
        <a href="{github_repo_url}" target="_blank" rel="noopener noreferrer" class="github-link">View on GitHub</a>
    </header>
    <main>
"""

HTML_TEMPLATE_END = """
    </main>
    <footer>
        <p>Generated by gen_index.py on {build_time}</p>
    </footer>
</body>
</html>
"""

def is_git_repository():
    """
    Check if the current directory is inside a Git repository.
    """
    try:
        subprocess.run(['git', 'status'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        print("Git is not installed or not found in PATH.")
        return False

def get_git_commit_time(file_path):
    """
    Retrieve the last commit time for a given file using Git.

    Args:
        file_path (str): The relative path to the file.

    Returns:
        str: The last commit datetime in "YYYY-MM-DD HH:MM:SS" format.
             Returns "N/A" if the file is untracked or an error occurs.
    """
    try:
        # Use git log to get the last commit date for the file
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%ci', '--', file_path],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        commit_date = result.stdout.strip()
        if commit_date:
            # Format the date
            dt = datetime.datetime.strptime(commit_date, "%Y-%m-%d %H:%M:%S %z")
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return "N/A"
    except subprocess.CalledProcessError:
        return "N/A"

def collect_pdfs(root_dir):
    """
    Traverse the root_dir and collect all PDF files organized by their directories.

    Args:
        root_dir (str): The root directory to start searching from.

    Returns:
        dict: A dictionary with directory names as keys and lists of PDF info as values.
    """
    pdf_dict = {}
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Skip hidden directories
        dirnames[:] = [d for d in dirnames if not d.startswith('.')]
        
        # Calculate relative directory path from root
        rel_dir = os.path.relpath(dirpath, root_dir)
        if rel_dir == ".":
            rel_dir = "Root"

        pdf_files = []
        for file in filenames:
            if file.lower().endswith('.pdf'):
                file_path = os.path.join(dirpath, file)
                rel_url = os.path.relpath(file_path, root_dir).replace('\\', '/')
                
                if is_git_repository():
                    rel_file_path = os.path.relpath(file_path, root_dir).replace('\\', '/')
                    commit_time = get_git_commit_time(rel_file_path)
                else:
                    # Fallback to filesystem mtime if not in a git repo
                    mtime = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                    commit_time = mtime.strftime("%Y-%m-%d %H:%M:%S")
                
                pdf_files.append({
                    'name': file,
                    'url': rel_url,
                    'mtime': commit_time
                })
        if pdf_files:
            # Sort PDF files alphabetically
            pdf_files.sort(key=lambda x: x['name'].lower())
            pdf_dict[rel_dir] = pdf_files

    # Sort directories alphabetically
    sorted_pdf_dict = dict(sorted(pdf_dict.items(), key=lambda x: x[0].lower()))
    return sorted_pdf_dict

def generate_html(pdf_dict, build_time, css_filename, github_repo_url):
    """
    Generate the complete HTML content.

    Args:
        pdf_dict (dict): Dictionary of directories and their PDF files.
        build_time (str): Timestamp of when the HTML was generated.
        css_filename (str): The CSS file name to link.
        github_repo_url (str): URL of the GitHub repository.

    Returns:
        str: The complete HTML content.
    """
    html_content = HTML_TEMPLATE_START.format(
        css_filename=css_filename,
        build_time=build_time,
        github_repo_url=github_repo_url,
        google_analytics_id=GOOGLE_ANALYTICS_ID
    )
    
    for directory, pdfs in pdf_dict.items():
        html_content += f"    <section>\n"
        html_content += f"        <h2>{directory}</h2>\n"
        html_content += f"        <ul>\n"
        for pdf in pdfs:
            html_content += f"            <li><a href=\"{pdf['url']}\" target=\"_blank\" rel=\"noopener noreferrer\">{pdf['name']}</a> <span class=\"mtime\">({pdf['mtime']})</span></li>\n"
        html_content += f"        </ul>\n"
        html_content += f"    </section>\n"

    html_content += HTML_TEMPLATE_END.format(build_time=build_time)
    return html_content

def generate_css(css_path):
    """
    Generate the CSS styling for the HTML page.

    Args:
        css_path (str): Path where the CSS file will be saved.
    """
    css_content = """
* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    font-family: Arial, sans-serif;
    background-color: #f4f4f4;
    color: #333;
    line-height: 1.6;
    padding: 20px;
}

header {
    text-align: center;
    margin-bottom: 40px;
    position: relative;
}

header h1 {
    font-size: 2.5em;
    margin-bottom: 10px;
}

header p {
    color: #666;
}

/* GitHub Link Styling */
.github-link {
    position: absolute;
    top: 20px;
    right: 20px;
    text-decoration: none;
    color: #fff;
    background-color: #24292e;
    padding: 10px 15px;
    border-radius: 5px;
    transition: background-color 0.3s ease;
}

.github-link:hover {
    background-color: #444;
}

main {
    max-width: 800px;
    margin: 0 auto;
}

section {
    background: #fff;
    padding: 20px;
    margin-bottom: 20px;
    border-radius: 5px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

section h2 {
    margin-bottom: 15px;
    color: #007acc;
}

ul {
    list-style: none;
}

li {
    padding: 10px 0;
    border-bottom: 1px solid #eee;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

li:last-child {
    border-bottom: none;
}

a {
    text-decoration: none;
    color: #333;
    transition: color 0.3s ease;
}

a:hover {
    color: #007acc;
}

.mtime {
    font-size: 0.9em;
    color: #999;
}

footer {
    text-align: center;
    margin-top: 40px;
    color: #666;
    font-size: 0.9em;
}

@media (max-width: 600px) {
    body {
        padding: 10px;
    }

    header h1 {
        font-size: 2em;
    }

    .github-link {
        position: static;
        display: inline-block;
        margin-top: 20px;
    }

    section {
        padding: 15px;
    }

    li {
        flex-direction: column;
        align-items: flex-start;
    }

    .mtime {
        margin-top: 5px;
    }
}
"""
    with open(css_path, 'w', encoding='utf-8') as css_file:
        css_file.write(css_content.strip())

def main():
    # Check if inside a Git repository
    git_repo = is_git_repository()
    if git_repo:
        print("Git repository detected. Using Git commit times for PDFs.")
    else:
        print("Not a Git repository or Git not installed. Falling back to filesystem modification times.")

    # Define root directory (current directory)
    root_dir = os.getcwd()

    # Collect PDF files with their last commit times
    pdf_dict = collect_pdfs(root_dir)

    # Get current timestamp
    build_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Generate CSS file
    css_path = os.path.join(root_dir, CSS_FILENAME)
    generate_css(css_path)

    # Generate HTML content with GitHub repository link
    html_content = generate_html(pdf_dict, build_time, CSS_FILENAME, GITHUB_REPO_URL)

    # Write to index.html
    index_path = os.path.join(root_dir, "index.html")
    with open(index_path, 'w', encoding='utf-8') as html_file:
        html_file.write(html_content)

    print(f"index.html and {CSS_FILENAME} have been generated successfully.")

if __name__ == "__main__":
    main()