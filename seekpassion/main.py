from __future__ import annotations

import argparse
import logging
from pathlib import Path

from rich.console import Console
from rich.table import Table

from seekpassion.config import load_config
from seekpassion.db.models import Job
from seekpassion.db.session import get_session, init_db
from seekpassion.discovery.company_board import build_scraper
from seekpassion.discovery.deduplicator import upsert_jobs
from seekpassion.evaluation.profile import load_profile
from seekpassion.evaluation.ranker import run_evaluation

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
console = Console()


def cmd_discover(args: argparse.Namespace) -> None:
    cfg = load_config(args.config)
    init_db(args.db)
    session = get_session()

    total_inserted = 0
    total_skipped = 0
    total_filtered = 0

    for company in cfg.companies:
        scraper = build_scraper(company.name, company.url, cfg.discovery.max_job_age_weeks)
        if scraper is None:
            continue
        console.print(f"[cyan]Scraping {company.name}…[/cyan]")
        raw_jobs = scraper.scrape()
        console.print(f"  Found {len(raw_jobs)} postings")
        inserted, skipped, filtered = upsert_jobs(
            raw_jobs, session,
            allowed_domains=cfg.discovery.domains,
            title_exclude=cfg.discovery.title_exclude,
        )
        total_inserted += inserted
        total_skipped += skipped
        total_filtered += filtered

    console.print(
        f"\n[green]Discovery complete:[/green] {total_inserted} new jobs inserted, "
        f"{total_skipped} duplicates skipped, {total_filtered} filtered out."
    )


def cmd_evaluate(args: argparse.Namespace) -> None:
    cfg = load_config(args.config)
    init_db(args.db)
    session = get_session()

    profile = load_profile(
        Path(cfg.resume.static_file),
        Path(cfg.resume.pool_file),
    )
    console.print(f"[cyan]Candidate:[/cyan] {profile.name} | {profile.total_years} yrs exp | "
                  f"Skills: {len(profile.skills)}")

    count = run_evaluation(profile, cfg, session)
    console.print(f"[green]Evaluation complete:[/green] {count} jobs evaluated.")


def cmd_list(args: argparse.Namespace) -> None:
    load_config(args.config)
    init_db(args.db)
    session = get_session()

    query = session.query(Job).filter(Job.status == "evaluated")
    if args.min_fit:
        query = query.filter(Job.fit_score >= args.min_fit)
    jobs = query.order_by(Job.ranking_score.desc()).limit(args.limit).all()

    if not jobs:
        console.print("[yellow]No evaluated jobs found.[/yellow]")
        return

    table = Table(title=f"Top {len(jobs)} Jobs by Ranking Score", show_lines=False)
    table.add_column("#", style="dim", width=3)
    table.add_column("Company", style="bold")
    table.add_column("Title")
    table.add_column("Fit", justify="right")
    table.add_column("Success", justify="right")
    table.add_column("Rank", justify="right", style="green")
    table.add_column("Remote")
    table.add_column("Location")

    for i, job in enumerate(jobs, 1):
        table.add_row(
            str(i),
            job.company,
            job.title,
            f"{job.fit_score:.0f}",
            f"{job.success_probability:.0f}",
            f"{job.ranking_score:.0f}",
            "yes" if job.remote else "no",
            job.location or "—",
        )

    console.print(table)


def cli() -> None:
    parser = argparse.ArgumentParser(prog="sp")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--db", default="seekpassion.db")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("discover", help="Scrape company boards for new jobs")

    sub.add_parser("evaluate", help="Evaluate and score all new jobs")

    list_p = sub.add_parser("list", help="Show ranked evaluated jobs")
    list_p.add_argument("--limit", type=int, default=20)
    list_p.add_argument("--min-fit", type=float, default=None)

    args = parser.parse_args()
    commands = {"discover": cmd_discover, "evaluate": cmd_evaluate, "list": cmd_list}
    commands[args.command](args)


if __name__ == "__main__":
    cli()
