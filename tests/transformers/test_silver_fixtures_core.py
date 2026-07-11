from pipelines.transformers.silver_fixtures_core import fetch_raw_fixtures


def test_fetch_raw_fixtures_query_filters_finished_matches():
    """Vérifie que la requête restreint bien aux matchs terminés (FT)."""
    from pipelines.transformers import silver_fixtures_core
    import inspect

    source = inspect.getsource(silver_fixtures_core.fetch_raw_fixtures)
    assert "status_short = 'FT'" in source