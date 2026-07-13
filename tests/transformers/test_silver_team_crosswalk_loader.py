"""
Tests de la logique de résolution du crosswalk d'équipes.

Contrairement aux flatteners RAW (données réelles obligatoires, structure
JSON externe à vérifier), ici la logique est déterministe et entièrement
contrôlée par nous : on teste avec de petits DataFrames construits à la main,
pour couvrir précisément chaque cas (match exact, divergent, non-matché, erreur).
"""

import pandas as pd
import pytest

from pipelines.transformers.silver_team_crosswalk_loader import build_crosswalk_rows


@pytest.fixture
def kaggle_df():
    return pd.DataFrame({
        "team_api_id": [1, 2, 3],
        "team_long_name": ["Arsenal", "FC Bayern Munich", "AC Ajaccio"],
    })


@pytest.fixture
def api_df():
    return pd.DataFrame({
        "team_id": [101, 102, 103, 104],
        "team_name": ["Arsenal", "Bayern Munich", "Ajaccio", "Brentford"],
    })


@pytest.fixture
def small_mapping():
    """Mapping isolé, indépendant du vrai crosswalk (99 clubs), pour tester
    la logique de résolution sans dépendre de données de production."""
    return {"Arsenal": "Arsenal", "Bayern Munich": "FC Bayern Munich", "Ajaccio": "AC Ajaccio"}


@pytest.fixture
def small_unmatched():
    return ["Brentford"]


class TestBuildCrosswalkRows:

    def test_nombre_de_lignes_egal_taille_du_mapping_complet(
        self, kaggle_df, api_df, small_mapping, small_unmatched
    ):
        """Une ligne par entrée du mapping (matchés + unmatched)."""
        df = build_crosswalk_rows(kaggle_df, api_df, small_mapping, small_unmatched)
        assert len(df) == len(small_mapping) + len(small_unmatched)

    def test_match_exact_resout_le_bon_id_des_deux_cotes(
        self, kaggle_df, api_df, small_mapping, small_unmatched
    ):
        df = build_crosswalk_rows(kaggle_df, api_df, small_mapping, small_unmatched)
        row = df[df["api_football_team_name"] == "Arsenal"].iloc[0]
        assert row["kaggle_team_api_id"] == 1
        assert row["api_football_team_id"] == 101
        assert row["match_confidence"] == "exact"

    def test_match_divergent_resout_le_bon_id_des_deux_cotes(
        self, kaggle_df, api_df, small_mapping, small_unmatched
    ):
        df = build_crosswalk_rows(kaggle_df, api_df, small_mapping, small_unmatched)
        row = df[df["api_football_team_name"] == "Bayern Munich"].iloc[0]
        assert row["kaggle_team_api_id"] == 2
        assert row["api_football_team_id"] == 102
        assert row["match_confidence"] == "manual_verified"

    def test_cas_ajaccio_ne_matche_pas_gfc_ajaccio(
        self, kaggle_df, api_df, small_mapping, small_unmatched
    ):
        df = build_crosswalk_rows(kaggle_df, api_df, small_mapping, small_unmatched)
        row = df[df["api_football_team_name"] == "Ajaccio"].iloc[0]
        assert row["kaggle_team_api_id"] == 3
        assert row["match_confidence"] == "manual_verified"

    def test_club_non_matche_a_des_ids_kaggle_null(
        self, kaggle_df, api_df, small_mapping, small_unmatched
    ):
        df = build_crosswalk_rows(kaggle_df, api_df, small_mapping, small_unmatched)
        row = df[df["api_football_team_name"] == "Brentford"].iloc[0]
        assert pd.isna(row["kaggle_team_api_id"])
        assert pd.isna(row["kaggle_team_name"])
        assert row["match_confidence"] == "unmatched"

    def test_nom_api_football_absent_leve_une_erreur_explicite(self, kaggle_df):
        """Si un club du mapping est absent du DataFrame API-Football fourni,
        doit planter bruyamment plutôt qu'insérer un id manquant en silence."""
        api_df_incomplet = pd.DataFrame({"team_id": [999], "team_name": ["Un Club Inconnu"]})
        mapping = {"Arsenal": "Arsenal"}
        with pytest.raises(ValueError, match="Arsenal"):
            build_crosswalk_rows(kaggle_df, api_df_incomplet, mapping, [])

    def test_nom_kaggle_absent_leve_une_erreur_explicite(self, api_df):
        """Si le nom Kaggle attendu par le mapping est absent du DataFrame Kaggle
        fourni, doit planter bruyamment plutôt qu'insérer un id manquant en silence."""
        kaggle_df_incomplet = pd.DataFrame({"team_api_id": [1], "team_long_name": ["Un Autre Club"]})
        mapping = {"Bayern Munich": "FC Bayern Munich"}
        with pytest.raises(ValueError, match="FC Bayern Munich"):
            build_crosswalk_rows(kaggle_df_incomplet, api_df, mapping, [])

    def test_utilise_le_vrai_mapping_de_production_par_defaut(self):
        """Sans mapping fourni, la fonction doit utiliser le vrai crosswalk
        (99 clubs) — filet de sécurité pour vérifier que le défaut est branché."""
        from pipelines.transformers.team_crosswalk import build_full_crosswalk, KNOWN_UNMATCHED
        full_mapping = build_full_crosswalk()
        # On construit des DataFrames complets couvrant tous les noms réels
        api_names = list(full_mapping.keys()) + KNOWN_UNMATCHED
        kaggle_names = list(full_mapping.values())
        api_df = pd.DataFrame({"team_id": range(len(api_names)), "team_name": api_names})
        kaggle_df = pd.DataFrame({"team_api_id": range(len(kaggle_names)), "team_long_name": kaggle_names})
        df = build_crosswalk_rows(kaggle_df, api_df)
        assert len(df) == len(full_mapping) + len(KNOWN_UNMATCHED)