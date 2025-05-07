"""Worker script to run ResearchManager."""
import asyncio
import sys
from pathlib import Path

from emailer import Emailer
from research_bot.manager import ResearchManager

if __name__ == "__main__":
    query = sys.argv[1]
    report = asyncio.run(ResearchManager().run(query))
    filename = report.filename
    with Path.open(f"research_reports/{filename}.md","w") as file:
        file.write(report.markdown_report)

    Emailer().send_email(
        report.filename,
        report.short_summary,
        f"research_reports/{filename}.md",
    )
