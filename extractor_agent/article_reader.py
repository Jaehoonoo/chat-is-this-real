from newspaper import Article, Config

user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36"
config = Config()
config.browser_user_agent = user_agent


def article_read_tool(url: str):
    """
    Params:
    url : str The URL of the article to extract. Must be a valid, reachable HTTP/HTTPS URL.

    Extract and parse an article from a URL. Returns a dictionary with the article summary and full text.
    """

    article = Article(url, config=config)
    article.download()
    article.parse()

    return {"article_summary": article.summary, "article_full_text": article.text}
