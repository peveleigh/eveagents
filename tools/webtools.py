"""Collection of tools for interacting with the web."""

from __future__ import annotations

import os
import subprocess

import requests
from agents import function_tool
from dotenv import load_dotenv
from exa_py import Exa

from tools.emailer import Emailer

load_dotenv()

@function_tool
def web_search(
    query: str,
    category: str = "all",
    language: str = "en",
    ) -> dict:
    """Perform a search using SearXNG API.

    Args:
        query (str): The search query
        category (str): Search category (all, images, videos, etc.)
        language (str): Language preference

    Returns:
        dict: Search results

    """
    engines = "brave,duckduckgo"

    params = {
        "q": query,
        "categories": category,
        "language": language,
        "engines": engines,
        "format": "json",
    }

    headers = {
        "User-Agent": str(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36",
        ),
    }

    instance = os.getenv("SEARXNG_URL")

    response = requests.get(
        f"{instance}/search",
        params=params,
        headers=headers,
        timeout=30,
    )

    if response.status_code == 200:
        return [
            {"url": item["url"], "title": item["title"], "content": item["content"]}
            for item in response.json()["results"]
        ]
    else:
        raise Exception(f"Error: {response.status_code} - {response.text}")

@function_tool
def email_tool(
    subject: str,
    body: str,
    attachment_path: str | None = None,
) -> bool:
    """Send an email.

    Args:
        subject: Subject of the email
        body: Body of the email
        attachment_path: Path to file to attach to email

    Returns:
            bool: True if email was sent successfully, False otherwise

    """
    recipient_email =  os.environ.get("RECIPIENT_EMAIL")
    if attachment_path:
        success = Emailer().send_email(
            recipient_email,
            subject,
            body,
            attachment_path,
        )
    else:
        success = Emailer().send_email(
            recipient_email,
            subject,
            body,
        )
    return success


@function_tool
def research(query: str) -> str:
    """Research a topic and send report to email."""
    cmd = f'python tools/research_worker.py "{query}"'
    subprocess.Popen(cmd, shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True)
    return "Running a research report. It should be available in your inbox shortly."

@function_tool
def exa_search(query: str) -> str:
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

web_tools = [web_search, web_scrape, email_tool]
