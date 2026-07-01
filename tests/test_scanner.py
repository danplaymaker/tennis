"""Tests for the live scanner's API-Tennis parsing logic."""

from src.live.scanner import (
    _current_set,
    _extract_spw,
    _game_had_deuce,
    _game_is_complete,
    _detect_surface,
)


class TestGameParsing:
    def test_deuce_detected(self):
        game = {"points": ["15-0", "30-0", "30-15", "30-30", "40-30", "40-40", "AD-40", "game"]}
        assert _game_had_deuce(game) is True

    def test_no_deuce(self):
        game = {"points": ["15-0", "30-0", "40-0", "game"]}
        assert _game_had_deuce(game) is False

    def test_game_complete_with_result(self):
        assert _game_is_complete({"result": "home"}) is True

    def test_game_complete_with_game_in_points(self):
        assert _game_is_complete({"points": ["15-0", "30-0", "40-0", "game"]}) is True

    def test_game_incomplete(self):
        assert _game_is_complete({"points": ["15-0", "30-0"]}) is False


class TestSetDetection:
    def test_set_from_status(self):
        assert _current_set({"event_status": "Set 3"}) == 3
        assert _current_set({"event_status": "Set 1"}) == 1

    def test_set_from_scores(self):
        event = {
            "event_status": "In Progress",
            "scores": {
                "1": {"score_home": "6", "score_away": "4"},
                "2": {"score_home": "3", "score_away": "2"},
                "game": {"score_home": "30", "score_away": "15"},
            },
        }
        assert _current_set(event) == 2


class TestSPWExtraction:
    def test_derives_from_stats(self):
        stats = [
            {"type": "1st Serve %", "home": "65%", "away": "60%"},
            {"type": "1st Serve Won %", "home": "75%", "away": "70%"},
            {"type": "2nd Serve Won %", "home": "50%", "away": "45%"},
        ]
        spw_h, spw_a = _extract_spw(stats)
        # home: 0.65*0.75 + 0.35*0.50 = 0.4875 + 0.175 = 0.6625
        assert abs(spw_h - 0.6625) < 0.001
        # away: 0.60*0.70 + 0.40*0.45 = 0.42 + 0.18 = 0.60
        assert abs(spw_a - 0.60) < 0.001

    def test_defaults_without_stats(self):
        spw_h, spw_a = _extract_spw([])
        assert spw_h == 0.62
        assert spw_a == 0.62

    def test_handles_none(self):
        spw_h, spw_a = _extract_spw(None)
        assert spw_h == 0.62


class TestSurfaceDetection:
    def test_wimbledon_is_grass(self):
        assert _detect_surface({"league_name": "ATP - Wimbledon"}) == "grass"

    def test_roland_garros_is_clay(self):
        assert _detect_surface({"league_name": "ATP - Roland Garros"}) == "clay"

    def test_unknown_defaults_hard(self):
        assert _detect_surface({"league_name": "ATP - US Open"}) == "hard"
