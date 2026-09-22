"""
This script collects all markdown files in the requirements folder and its subfolders, and generates one html document with URSs, FSs, and tests.
- URSs are defined in `urs` folder as markdown files.
- FSs and tests are defined in `fs` folder as markdown files.

The generated html document is saved as `Consumer_API_Traceability.html` in the requirements folder.
"""

import html
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import markdown
from bs4 import BeautifulSoup
from jinja2 import Template

# Configure logging
log_format = "%(levelname)-8s %(message)s"
logging.basicConfig(level=logging.INFO, format=log_format)
logger = logging.getLogger(__name__)

# Define paths
BASE_DIR = Path(__file__).resolve().parent.parent
REQUIREMENTS_DIR = BASE_DIR / "requirements"
OUTPUT_FILE = REQUIREMENTS_DIR / "Consumer_API_Traceability.html"
URS_DIR = REQUIREMENTS_DIR / "urs"
FS_DIR = REQUIREMENTS_DIR / "fs"
TEMPLATE_FILE = REQUIREMENTS_DIR / "traceability_template.html"

HTML_PARSER = "html.parser"


def collect_markdown_files(directory):
    """Collect all markdown files in the given directory and its subdirectories."""
    md_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".md"):
                md_files.append(Path(root) / file)
    return md_files


def parse_markdown_file(file_path) -> str:
    """Parse a markdown file and return its HTML content."""
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    html = markdown.markdown(text, extensions=["fenced_code", "tables"])
    return html


def extract_section_headers_and_content(
    html_content: str, html_tag: str = "h1"
) -> list[tuple[str, list[Any]]]:
    """Extract all IDs from the HTML content."""
    soup = BeautifulSoup(html_content, HTML_PARSER)
    sections = []
    for html_element in soup.find_all(html_tag):
        text = html_element.get_text().strip()
        if text.startswith("FS-") or text.startswith("URS-"):
            # Extract all content until the next `html_tag` or end of document
            content = []
            for sibling in html_element.find_next_siblings():
                if sibling.name in ["h1", html_tag]:
                    break
                content.append(sibling)
            sections.append((text, content))
    return sections


def extract_fs_titles_and_tests(html_content: str):
    """Extract FS titles and their corresponding tests from the HTML content."""
    soup = BeautifulSoup(html_content, HTML_PARSER)
    fs_titles_and_tests = []

    for html_element in soup.find_all("h2"):
        text = html_element.get_text().strip()
        # Only consider headers that start with "FS-"
        # Find all sibling h3 elements with text `Test coverage` until the next h2 or end of document
        if text.startswith("FS-"):
            for sibling in html_element.find_next_siblings():
                if sibling.name == "h2":
                    break
                if (
                    sibling.name == "h3"
                    and sibling.get_text().strip().lower() == "test coverage"
                ):
                    # Collect all sibling <table> elements until the next h3 or h2
                    for table_sibling in sibling.find_next_siblings():
                        if table_sibling.name in ["h2", "h3"]:
                            break
                        if table_sibling.name == "table":
                            rows = table_sibling.find_all("tr")
                            tests_list = []
                            for row in rows:
                                cols = row.find_all("td")
                                if len(cols) >= 2:
                                    test_file = cols[0].get_text().strip()
                                    test_method = cols[1].get_text().strip()
                                    tests_list.append(
                                        {"file": test_file, "method": test_method}
                                    )

                            fs_titles_and_tests.append(
                                (text, table_sibling, tests_list)
                            )
    return fs_titles_and_tests


def extract_id_and_title(html_content: str):
    """Extract the ID and title from the HTML content."""
    soup = BeautifulSoup(html_content, HTML_PARSER)
    h1 = soup.find("h1")
    if h1:
        title = h1.get_text(strip=True)
        id_match = re.search(r"\[(.*?)\]", title)
        if id_match:
            id_ = id_match.group(1)
            title = title.replace(f"[{id_}]", "").strip()
            return id_, title
    return None, None


def generate_html(full_traceability, warnings) -> str:
    """Generate the final HTML document using Jinja2 template."""
    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        template_str = f.read()
        template = Template(template_str, autoescape=True)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        html = template.render(
            now=now, full_traceability=full_traceability, warnings=warnings
        )
        return html


def main():
    # Collect markdown files
    urs_files = collect_markdown_files(URS_DIR)
    fs_files = collect_markdown_files(FS_DIR)

    full_traceability: list[dict[str, Any]] = []

    # Parse URS files
    collect_urs_traceability(urs_files, full_traceability)

    # Parse FS files
    all_fs_ids = collect_fs_traceability(fs_files, full_traceability)

    # Generate HTML sections for each URS with its FSs
    full_traceability_html = generate_traceability_html(full_traceability)

    warnings = get_warnings_html(full_traceability, all_fs_ids)

    # Generate final HTML
    final_html = generate_html("\n".join(full_traceability_html), warnings=warnings)

    # Save to output file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(final_html)

    logger.info(f"Traceability document generated at {OUTPUT_FILE}")


def collect_fs_traceability(fs_files, full_traceability):
    all_fs_ids = set()
    for fs_file in fs_files:
        try:
            html_content = parse_markdown_file(fs_file)
            sections = extract_section_headers_and_content(html_content, "h2")
            fs_titles_and_tests = extract_fs_titles_and_tests(html_content)

            if sections:
                for fs_title, section_content in sections:
                    # Extract FS and URS IDs from 'FS-... [URS-...]'
                    fs_id = fs_title[: fs_title.index("[")].strip()
                    if fs_id in all_fs_ids:
                        logger.warning(f"Duplicate FS ID {fs_id} found in {fs_file}")
                    all_fs_ids.add(fs_id)
                    urs_id = fs_title[
                        fs_title.index("[") + 1 : fs_title.index("]")
                    ].strip()
                    fs_tests = [
                        {"html": tests_html, "list": tests_list}
                        for title, tests_html, tests_list in fs_titles_and_tests
                        if title == fs_title
                    ]

                    # Link FS to URS in full_traceability dict list
                    for entry in full_traceability:
                        if entry["urs_id"] == urs_id:
                            entry["fs_list"].append(
                                {
                                    "fs_id": fs_id,
                                    "type": "FS",
                                    "text": "\n".join(
                                        [
                                            section_content.prettify()
                                            for section_content in section_content
                                        ]
                                    ),
                                    "tests_html": (
                                        fs_tests[0]["html"] if fs_tests else ""
                                    ),
                                    "tests_list": (
                                        fs_tests[0]["list"] if fs_tests else []
                                    ),
                                }
                            )
            else:
                logger.warning(f"No valid FS sections found in {fs_file}")
        except Exception as e:
            logger.error(f"Error parsing {fs_file}: {e}")
    return all_fs_ids


def collect_urs_traceability(urs_files, full_traceability):
    for urs_file in urs_files:
        try:
            html_content = parse_markdown_file(urs_file)
            sections = extract_section_headers_and_content(html_content, "h1")
            if sections:
                for urs_id, section_content in sections:
                    full_traceability.append(
                        {
                            "urs_id": urs_id,
                            "type": "URS",
                            "text": "\n".join(
                                [
                                    section_content.prettify()
                                    for section_content in section_content
                                ]
                            ),
                            "fs_list": [],
                        }
                    )
            else:
                logger.warning(f"No valid URS sections found in {urs_file}")
        except Exception as e:
            logger.error(f"Error parsing {urs_file}: {e}")


def get_warnings_html(
    full_traceability: list[dict[str, Any]], all_fs_ids: set[str] = set()
) -> str:
    """Generate warnings for FSs without tests/URS and URSs without FSs."""
    urs_no_fs = "URSs without linked FSs"
    fs_no_urs = "FSs without linked URS"
    fs_no_tests = "FSs without linked tests"
    non_existent_tests = "Non-existent tests"

    tests = get_all_tests()

    warnings: dict[str, list[str]] = {
        urs_no_fs: [],
        fs_no_urs: [],
        fs_no_tests: [],
        non_existent_tests: [],
    }

    for entry in full_traceability:
        # Check for URSs that do not have any linked FSs
        if not entry["fs_list"]:
            warning_msg = f"URS {entry['urs_id']} has no linked FS"
            logger.warning(warning_msg)
            warnings[urs_no_fs].append(entry["urs_id"])

        # Check for FSs that do not have any linked tests
        for fs in entry["fs_list"]:
            if not fs["tests_html"]:
                warning_msg = f"FS {fs['fs_id']} has no linked tests"
                logger.warning(warning_msg)
                warnings[fs_no_tests].append(fs["fs_id"])

        # Check for tests that do not exist in the tests folder
        test_names = []
        for filename, methods in [(t["file"], t["methods"]) for t in tests]:
            for method in methods:
                test_names.append(f"{filename}::{method}")

        for fs in entry["fs_list"]:
            if fs["tests_list"]:
                for test in fs["tests_list"]:
                    test_method = f"{test['file']}::{test['method']}"
                    if test_method not in test_names:
                        warning_msg = f"Test {test_method} does not exist"
                        logger.warning(warning_msg)
                        warnings[non_existent_tests].append(test_method)

    # Check for FSs that are not linked to any URS
    linked_fs_ids = set()
    for entry in full_traceability:
        for fs in entry["fs_list"]:
            linked_fs_ids.add(fs["fs_id"])
    unlinked_fs_ids = all_fs_ids - linked_fs_ids
    for fs_id in unlinked_fs_ids:
        warning_msg = f"FS {fs_id} is not linked to any URS"
        logger.warning(warning_msg)
        warnings[fs_no_urs].append(fs_id)

    warnings_html = []
    for category, problems in warnings.items():
        if problems:
            warnings_html.append(f"<h3>{html.escape(category)}</h3><ul>")
            for problem in problems:
                warnings_html.append(f"<li>{html.escape(problem)}</li>")
            warnings_html.append("</ul>")

    return "".join(warnings_html) if warnings_html else "<h3>-- None --</h3>"


def get_all_tests() -> list[dict[str, Any]]:
    """Get a list of all python tests files and test methods that exist in the `tests` folder.

    Returns:
        list[dict]: List of test files and method names. Each item is a dict with keys `file` and `methods`.
    """
    tests_dir = Path(BASE_DIR / "tests")

    tests = []
    for root, _, files in os.walk(tests_dir):
        for file in files:
            if file.endswith(".py"):
                file_path = Path(root) / file
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    method_names = re.findall(r"def (test_\w+)\s*\(", content)
                    tests.append(
                        {
                            "file": str(file_path.relative_to(BASE_DIR)),
                            "methods": method_names,
                        }
                    )
    return tests


def generate_traceability_html(full_traceability: list[Any]) -> list[str]:
    """Generate HTML representing each URS and its FSs."""
    full_traceability_html = []
    for urs_idx, item in enumerate(full_traceability):
        urs_section = f"""
        <h1 class="urs" id="{html.escape(item["urs_id"])}">{urs_idx+1} {html.escape(item["urs_id"])}</h1> 
        <div class="urs-text">{item["text"]}</div>
        """

        # List all FSs under this URS
        fs_sections = []
        for fs_idx, fs in enumerate(item["fs_list"]):
            fs_section = f"""
            <h2 class="fs" id="{html.escape(fs["fs_id"])}">{urs_idx+1}.{fs_idx+1} {html.escape(fs["fs_id"])}</h2>
            <div class="fs-text">{fs["text"]}</div>
            <div class="fs-tests">{fs["tests_html"]}</div>
            """
            fs_sections.append(fs_section)

        full_traceability_html.append(
            urs_section + '<div class="fs-list">' + "".join(fs_sections) + "</div>"
        )

    return full_traceability_html


if __name__ == "__main__":
    main()
