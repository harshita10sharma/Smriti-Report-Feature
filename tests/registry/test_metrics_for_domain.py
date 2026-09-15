from analysis.models.enums import Domain
from analysis.registry import METRICS, metrics_for_domain


def test_every_domain_returns_only_metrics_assigned_to_it() -> None:
    for domain in Domain:
        for metric in metrics_for_domain(domain):
            assert metric.domain == domain


def test_metrics_for_domain_covers_every_registered_metric_exactly_once() -> None:
    total = sum(len(metrics_for_domain(domain)) for domain in Domain)
    assert total == len(METRICS)


def test_current_registry_counts_per_domain() -> None:
    # Locks in today's real registry shape so a future registry edit
    # that silently changes domain membership is caught by a failing
    # test rather than discovered downstream.
    assert len(metrics_for_domain(Domain.MEMORY)) == 9
    assert len(metrics_for_domain(Domain.ATTENTION)) == 6
    assert len(metrics_for_domain(Domain.EXECUTIVE)) == 4
    assert len(metrics_for_domain(Domain.VISUOSPATIAL)) == 12
    assert len(metrics_for_domain(Domain.LANGUAGE)) == 3


def test_no_domain_is_empty() -> None:
    for domain in Domain:
        assert len(metrics_for_domain(domain)) > 0
