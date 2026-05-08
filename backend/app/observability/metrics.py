from prometheus_client import Counter, Histogram, generate_latest, REGISTRY
from typing import Dict

review_total = Counter(
    "shipguard_review_total",
    "Total number of reviews",
    labelnames=["mode", "verdict"],
)

review_duration = Histogram(
    "shipguard_review_duration_seconds",
    "Review duration in seconds",
    labelnames=["mode"],
    buckets=(1, 2, 5, 10, 15, 20, 30, 60),
)

upload_rejected_total = Counter(
    "shipguard_upload_rejected_total",
    "Total number of upload rejections",
    labelnames=["reason"],
)

security_findings_total = Counter(
    "shipguard_security_findings_total",
    "Total number of security findings",
    labelnames=["severity"],
)

llm_review_total = Counter(
    "shipguard_llm_review_total",
    "Total number of LLM review attempts",
    labelnames=["status"],
)

report_export_total = Counter(
    "shipguard_report_export_total",
    "Total number of report exports",
    labelnames=["format"],
)


def observe_review(mode: str, verdict: str, duration: float, findings: Dict[str, int]):
    review_total.labels(mode=mode, verdict=verdict).inc()
    review_duration.labels(mode=mode).observe(duration)
    for severity, count in findings.items():
        if count > 0:
            security_findings_total.labels(severity=severity.lower()).inc(count)


def observe_upload_rejected(reason: str):
    upload_rejected_total.labels(reason=reason).inc()


def observe_llm_review(status: str):
    llm_review_total.labels(status=status).inc()


def observe_report_export(fmt: str = "markdown"):
    report_export_total.labels(format=fmt).inc()


def get_metrics() -> str:
    return generate_latest(REGISTRY).decode("utf-8")
