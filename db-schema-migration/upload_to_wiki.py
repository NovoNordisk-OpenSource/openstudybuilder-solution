import os
import sys
import requests
import re
import json
import urllib
import base64
import uuid
import datetime
from zipfile import ZipFile, ZIP_DEFLATED

WIKI_PERSONAL_ACCESS_TOKEN = os.environ.get("WIKI_PERSONAL_ACCESS_TOKEN", None)
WIKI_API_TOKEN = os.environ.get("WIKI_API_TOKEN", None)

PROJECT = os.environ.get("PROJECT", "Clinical-MDR")
WIKI_IDENTIFIER = os.environ.get("WIKI_IDENTIFIER", "Clinical-MDR.wiki")

MD_FILE = sys.argv[1]
MD_DIR = os.path.dirname(MD_FILE)

RUN_UUID = str(uuid.uuid4())

WIKI_PATH = os.environ.get("WIKI_PATH", "testing")
WIKI_PAGE_NAME = os.environ.get("WIKI_PAGE_NAME", "Correction")


def make_headers(is_json=True):
    if WIKI_PERSONAL_ACCESS_TOKEN:
        token = str(
            base64.b64encode(bytes(":" + WIKI_PERSONAL_ACCESS_TOKEN, "ascii")), "ascii"
        )
        auth_type = "Basic"
    elif WIKI_API_TOKEN:
        token = WIKI_API_TOKEN
        auth_type = "Bearer"
    else:
        raise RuntimeError("No Wiki api token found!")
    headers = {
        "Authorization": f"{auth_type} {token}",
        "Content-Type": "application/octet-stream",
    }
    if is_json:
        headers["Content-Type"] = "application/json"
    return headers


def upload_attachment(json_name):
    # Check if the file exists
    json_path = os.path.join(MD_DIR, json_name)
    json_path_zipped = os.path.join(MD_DIR, json_name + ".zip")

    if not os.path.exists(json_path):
        print(f"File '{json_name}' does not exist, skipping upload.")
        return None

    print(f"Upload attachment '{json_name}'")
    project = urllib.parse.quote(PROJECT.encode("utf-8"))
    wiki_identifier = urllib.parse.quote(WIKI_IDENTIFIER.encode("utf-8"))

    # All attachments are stored in a single folder,
    # so we need to make sure that the name is unique.
    # Insert the UUID between the name and the json ending.
    base_name, extension = os.path.splitext(json_name)
    unique_name = f"{base_name}-{RUN_UUID}{extension}.zip"

    name = urllib.parse.quote(unique_name.encode("utf-8"))
    wiki_url = f"https://dev.azure.com/orgremoved/{project}/_apis/wiki/wikis/{wiki_identifier}/attachments?name={name}&api-version=7.0"
    headers = make_headers(is_json=False)
    
    print(f"Zip '{json_path} into '{json_path_zipped}'")
    json_zipped = ZipFile(json_path_zipped, "w", ZIP_DEFLATED)
    json_zipped.write(json_path)
    json_zipped.close()    
    
    # Upload zip file
    with open(json_path_zipped, "rb") as f:
        data = base64.b64encode(f.read())

        req = requests.put(
            wiki_url,
            headers=headers,
            data=data,
        )

        if req.ok:
            reply = req.json()
            new_link = reply["path"]
        else:
            print(f"Error uploading attachment: {req.status_code} {req.reason}")
            new_link = None
        return new_link


def create_page(data, wiki_path):
    print(f"Create page at path '{wiki_path}'")
    wiki_url = make_page_url(wiki_path)
    req = requests.put(
        wiki_url, headers=make_headers(), data=json.dumps({"content": data})
    )
    print(req.status_code, req.reason)


def get_page(path):
    wiki_url = make_page_url(path)
    return requests.get(wiki_url, headers=make_headers())


def make_page_url(path):
    project = urllib.parse.quote(PROJECT.encode("utf-8"))
    wiki_identifier = urllib.parse.quote(WIKI_IDENTIFIER.encode("utf-8"))
    encoded_path = urllib.parse.quote(path.encode("utf-8"))
    return f"https://dev.azure.com/orgremoved/{project}/_apis/wiki/wikis/{wiki_identifier}/pages?path={encoded_path}&api-version=7.0"


def create_page_with_full_path(data, wiki_path):
    intermediate_pages = wiki_path.split("/")[:-1]
    page_path = ""
    for page in intermediate_pages:
        page_path += page
        req = get_page(page_path)
        if req.status_code == 404:
            print(f"Create intermediate page at path '{page_path}'")
            placeholder_data = f"# {page}\n\n(placeholder)\n"
            create_page(placeholder_data, page_path)
        else:
            print(f"Intermediate page at path '{page_path}' already exists")
        page_path += "/"
    create_page(data, wiki_path)


# Check if the line contains a link to a json file.
# If it does, upload the file to the wiki and update the link.
def upload_attachment_and_update_json_link(line):
    regex = re.compile(r"\[.*\.json\]\((.*\.json)\)")
    match = regex.search(line)
    if match:
        json_name = match.group(1)
        if not os.path.exists(os.path.join(MD_DIR, json_name)):
            print(f"File '{json_name}' does not exist, not updating link")
        else:            
            new_link = upload_attachment(json_name)
            if new_link is not None:
                # update the link
                print(f"Update link to '{json_name}': {new_link}")
                line = re.sub(r"\[.*\]\(.*\)", f"[{json_name}]({new_link})", line)
            else:
                print(f"Failed to upload attachment '{json_name}'")
    return line


def main():
    print(f"Processing markdown file '{MD_FILE}'")
    new_md = ""

    with open(MD_FILE, "r") as f:
        markdown_lines = f.readlines()
        for line in markdown_lines:
            # Skip any line that starts with "> " as these are block quotes
            if not line.startswith("> "):
                line = upload_attachment_and_update_json_link(line)
            new_md += line

    # Create a page name with todays date
    now = datetime.datetime.now()
    formatted_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    create_page_with_full_path(new_md, f"{WIKI_PATH}/{WIKI_PAGE_NAME} {formatted_datetime}")

if __name__ == "__main__":
    main()

