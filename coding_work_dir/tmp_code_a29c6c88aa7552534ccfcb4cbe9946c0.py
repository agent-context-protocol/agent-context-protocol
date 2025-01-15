
import requests

def get_total_edits(page_title, start_date, end_date):
    endpoint = "https://wikimedia.org/api/rest_v1/metrics/edits/per-page/en.wikipedia/all-editor-types/all-page-types/daily"
    params = {
        "start": start_date,
        "end": end_date
    }
    response = requests.get(f"{endpoint}/{page_title}", params=params)
    if response.status_code == 200:
        data = response.json()
        total_edits = sum(item['edits'] for item in data['items'])
        return total_edits
    else:
        return None

page_title = "Antidisestablishmentarianism"
start_date = "20010101"  # Wikipedia's inception for consistency
end_date = "20230630"

total_edits = get_total_edits(page_title, start_date, end_date)

print(total_edits)
