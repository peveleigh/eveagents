"""Worker script to run ResearchManager."""
import asyncio
import re
import sys
from pathlib import Path

from emailer import Emailer
from research_bot.manager import ResearchManager

if __name__ == "__main__":
    query = sys.argv[1]
    report = asyncio.run(ResearchManager().run(query))
    filename = re.sub(r"[^A-Za-z0-9 _-]", "_", report.filename).strip("._ ")
    if not filename:
        filename = "report"
    reports_dir = Path("research_reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / f"{filename}.md"
    with report_path.open("w", encoding="utf-8") as file:
        file.write(report.markdown_report)

    Emailer().send_email(
        report.filename,
        report.short_summary,
        str(report_path),
    )
