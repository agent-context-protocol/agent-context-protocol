# flake8: noqa
NEWS_API_TOP_HEADLINES_DOCS = """BASE URL: https://newsapi.org/v2/top-headlines

API Documentation:
The `/v2/top-headlines` endpoint provides breaking news headlines from various sources, blogs, and categories. You can filter the response using different parameters listed below.

Parameter	Format	Required	Default	Description
apiKey	String	Yes		Your API key to authenticate the request.
country	String	No		Returns headlines from a specific country. Options include ae, ar, at, au, be, bg, br, ca, cn, co, cu, cz, de, eg, fr, gb, gr, hk, hu, id, ie, il, in, it, jp, kr, lt, lv, ma, mx, my, ng, nl, no, nz, ph, pl, pt, ro, rs, ru, sa, se, sg, si, sk, th, tr, tw, ua, us, ve, za.
category	String	No		Filters news by category. Available options: business, entertainment, general, health, science, sports, technology.
sources	String	No		Returns headlines from specific news sources or blogs. Use `/sources` endpoint to retrieve valid source identifiers.
q	String	No		Keywords or phrases to search within headlines and descriptions.
pageSize	Integer	No	20	Number of results to return per page (maximum 100).
page	Integer	No	1	Page number to paginate through the results.

Example Request:
GET https://newsapi.org/v2/top-headlines?country=us&category=business&apiKey=YOUR_API_KEY

Example Response:
{
  "status": "ok",
  "totalResults": 34,
  "articles": [
    {
      "source": { "id": "bbc-news", "name": "BBC News" },
      "author": "BBC News",
      "title": "Example Headline",
      "description": "Short description of the news article.",
      "url": "https://www.bbc.co.uk/news/example",
      "urlToImage": "https://www.bbc.co.uk/news/example.jpg",
      "publishedAt": "2024-09-09T09:00:00Z",
      "content": "Full content of the news article."
    },
    ...
  ]
}
"""
