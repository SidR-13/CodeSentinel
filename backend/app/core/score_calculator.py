SEVERITY_DEDUCTIONS = {
    "CRITICAL": 25,
    "HIGH": 10,
    "MEDIUM": 5,
    "LOW": 2,
}


def calculate_score(review_data: dict) -> float:
    score = 100.0
    issue_categories = ["security_issues", "bugs", "quality_issues"]

    for category in issue_categories:
        for issue in review_data.get(category, []):
            severity = issue.get("severity", "LOW").upper()
            score -= SEVERITY_DEDUCTIONS.get(severity, 2)

    # Cross-file issues count as MEDIUM each
    for _ in review_data.get("cross_file_issues", []):
        score -= SEVERITY_DEDUCTIONS["MEDIUM"]

    return max(0.0, round(score, 1))


def count_issues(review_data: dict) -> tuple[int, int]:
    """Returns (total_issues, critical_issues)."""
    total = 0
    critical = 0
    for category in ["security_issues", "bugs", "quality_issues"]:
        for issue in review_data.get(category, []):
            total += 1
            if issue.get("severity", "").upper() == "CRITICAL":
                critical += 1
    total += len(review_data.get("cross_file_issues", []))
    return total, critical
