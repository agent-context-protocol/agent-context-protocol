# flake8: noqa
NEWS_API_DOCS = """
BASE URL: https://newsapi.org/v2/everything

API Documentation
The /v2/everything endpoint allows searching for articles that have been published by over 150,000 news sources within the past 5 years. This endpoint is ideal for detailed news analysis or discovery across a wide range of topics. URL parameters for this endpoint are as follows:

Parameter       Type        Required    Default Description
q               String      Yes         None    The search query or keywords. You can also use operators like AND, OR, NOT.
from            Date        No          None    The start date for the results. Articles older than this date will not be returned.
to              Date        No          None    The end date for the results. Articles published after this date will not be returned.
sortBy          String      No          publishedAt  The sorting order for the results. Options include relevancy, popularity, and publishedAt.
language        String      No          en      The language of the articles returned. Supported options include en, es, de, fr, and more.
domains         String      No          None    Restrict articles to specific domains (e.g., techcrunch.com, engadget.com).
excludeDomains  String      No          None    Exclude articles from specific domains.
pageSize        Integer     No          20      The number of results per page. Maximum is 100.
page            Integer     No          1       Use this to paginate through results.

Authentication:
You need an API key to use the NewsAPI endpoints. Authentication is done via the `X-Api-Key` header, which is sent with every request. Get your API key by signing up on the website.

Response Format:
The API returns results in JSON format. Each result includes the article’s title, author, source, URL, publication date, and a snippet of content.

Example Request:
GET https://newsapi.org/v2/everything?q=Apple&from=2022-01-01&sortBy=popularity&apiKey=YOUR_API_KEY

For more details, visit: https://newsapi.org/docs/endpoints/everything
"""
