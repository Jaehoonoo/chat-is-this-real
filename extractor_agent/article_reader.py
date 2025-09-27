from newspaper import Article, Config

user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36"
config = Config()
config.browser_user_agent = user_agent


def extract_article(url):
    """
    Extract and parse an article from a URL.
    This function constructs an Article object (using the surrounding module's Article class
    and config variable), downloads the article content from the provided URL, parses it,
    and returns a concise summary together with the full text.
    Parameters
    ----------
    url : str
        The URL of the article to extract. Must be a valid, reachable HTTP/HTTPS URL.
    Returns
    -------
    tuple[str, str]
        A 2-tuple (summary, text) where:
        - summary: a short, extracted summary of the article (may be empty if the extractor
          cannot produce a summary).
        - text: the full article text extracted from the page.
    Raises
    ------
    Exception
        Propagates any exceptions raised by the Article object (for example network errors,
        parse errors, or configuration issues). Callers should catch exceptions appropriate
        to their runtime environment.
    Notes
    -----
    - The function depends on an Article class and a config variable available in the
      module scope; ensure they are imported or defined before calling.
    - Behavior (quality of extraction and summary) depends on the underlying Article
      implementation and its configuration.
    Examples
    --------
    >>> summary, text = extract_article("https://example.com/news/article")
    """

    article = Article(url, config=config)
    article.download()
    article.parse()
    return article.summary, article.text
