"""Research report manager."""
from __future__ import annotations

import asyncio
import logging

from agents import Runner, gen_trace_id, trace

from .researchagents.planner_agent import WebSearchItem, WebSearchPlan, planner_agent
from .researchagents.search_agent import search_agent
from .researchagents.writer_agent import ReportData, writer_agent

logger = logging.getLogger(__name__)

class ResearchManager:
    """Research Manager class."""

    def __init__(self) -> None:
        """Initialize."""

    async def run(self, query: str) -> ReportData:
        """Run research report."""
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            search_plan = await self._plan_searches(query)
            search_results = await self._perform_searches(search_plan)
            return await self._write_report(query, search_results)

    async def _plan_searches(self, query: str) -> WebSearchPlan:
        result = await Runner.run(
            planner_agent,
            f"Query: {query}",
        )
        return result.final_output_as(WebSearchPlan)

    async def _perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        tasks = [
            asyncio.create_task(self._search(item))
            for item in search_plan.searches[:2]
        ]
        results = []
        for task in asyncio.as_completed(tasks):
            result = await task
            if result is not None:
                results.append(result)
        return results

    async def _search(self, item: WebSearchItem) -> str | None:
        msg = f"Search term: {item.query}\nReason for searching: {item.reason}"
        try:
            result = await Runner.run(
                search_agent,
                msg,
            )
            return str(result.final_output)
        except Exception:
            logger.exception("Failed to perform search.")
            return None

    async def _write_report(self, query: str, search_results: list[str]) -> ReportData:
        msg = f"Original query: {query}\nSummarized search results: {search_results}"
        result = await Runner.run(
            writer_agent,
            msg,
        )
        return result.final_output_as(ReportData)
