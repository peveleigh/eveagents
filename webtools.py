"""Collection of tools for interacting with the web."""

import os

import requests
from agents import function_tool
from dotenv import load_dotenv
from exa_py import Exa

load_dotenv()


@function_tool
def web_search(query: str) -> str:
    """Search the web for information.

    Args:
        query: Search query

    """
    exa = Exa(os.getenv("EXA_API_KEY"))
    return exa.search(query, num_results=3)

@function_tool
def web_scrape(url: str) -> str:
    """Scrape and process a web page using r.jina.ai.

    Args:
        url: The URL of the web page to scrape.

    Returns:
        The scraped and processed content without the Links/Buttons section,
        or an error message.

    """
    jina_url = f"https://r.jina.ai/{url}"

    headers = {
        "X-No-Cache": "true",
        "X-With-Images-Summary": "true",
        "X-With-Links-Summary": "true",
    }

    try:
        response = requests.get(jina_url, headers=headers, timeout=30)
        response.raise_for_status()

        # Extract content and remove Links/Buttons section as its too many tokens
        content = response.text
        links_section_start = content.rfind("Images:")
        if links_section_start != -1:
            content = content[:links_section_start].strip()
    except requests.RequestException as e:
        return f"Error scraping web page: {e!s}"

    return content

web_tools = [web_search, web_scrape]
