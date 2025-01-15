
import requests

def get_wikipedia_edit_count(page_title):
    S = requests.Session()
    URL = "https://en.wikipedia.org/w/api.php"

    PARAMS = {
        "action": "query",
        "format": "json",
        "prop": "revisions",
        "titles": page_title,
        "rvlimit": "max",
        "rvprop": "ids|timestamp"
    }

    response = S.get(url=URL, params=PARAMS)
    data = response.json()

    pages = data['query']['pages']
    for page_id in pages:
        revisions = pages[page_id].get('revisions', [])
        return len(revisions)

edit_count = get_wikipedia_edit_count("Antidisestablishmentarianism")
print("Edit count for 'Antidisestablishmentarianism':", edit_count)
print("Approximately 500 edits:", edit_count == 500)
