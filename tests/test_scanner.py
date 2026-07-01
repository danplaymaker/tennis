"""Tests for the live scanner's API-Tennis parsing logic."""

from src.live.scanner import (
    _current_set,
    _extract_spw_from_pbp,
    _game_had_deuce,
    _game_is_complete,
    _detect_surface,
    _player_name,
)


class TestPlayerName:
    def test_first_player(self):
        event = {"event_first_player": "Sinner J.", "event_second_player": "Djokovic N."}
        assert _player_name(event, "first") == "Sinner J."
        assert _player_name(event, "second") == "Djokovic N."

    def test_fallback_to_home_away(self):
        event = {"event_home_team": "Player Home"}
        assert _player_name(event, "first") == "Player Home"

    def test_default(self):
        assert _player_name({}, "first") == "Player A"
        assert _player_name({}, "second") == "Player B"


class TestGameParsing:
    def test_deuce_detected_dict_points(self):
        game = {"points": [
            {"score": "15 - 0"}, {"score": "30 - 0"}, {"score": "30 - 15"},
            {"score": "30 - 30"}, {"score": "40 - 30"}, {"score": "40 - 40"},
            {"score": "Ad - 40"}, {"score": "game"},
        ]}
        assert _game_had_deuce(game) is True

    def test_deuce_detected_compact_format(self):
        game = {"points": [
            {"score": "15-0"}, {"score": "30-0"}, {"score": "40-0"},
            {"score": "40-15"}, {"score": "40-30"}, {"score": "40-40"},
        ]}
        assert _game_had_deuce(game) is True

    def test_no_deuce(self):
        game = {"points": [
            {"score": "15 - 0"}, {"score": "30 - 0"}, {"score": "40 - 0"}, {"score": "game"},
        ]}
        assert _game_had_deuce(game) is False

    def test_deuce_from_string_points(self):
        game = {"points": "15-0 30-0 40-0 40-15 40-30 40 - 40 Ad-40 game"}
        assert _game_had_deuce(game) is True

    def test_game_complete_with_serve_winner(self):
        assert _game_is_complete({"serve_winner": "First Player"}) is True

    def test_game_complete_with_serve_lost(self):
        assert _game_is_complete({"serve_lost": "First Player"}) is True

    def test_game_complete_with_result(self):
        assert _game_is_complete({"result": "First Player"}) is True

    def test_game_complete_with_game_in_points(self):
        assert _game_is_complete({"points": [{"score": "game"}]}) is True

    def test_game_incomplete(self):
        assert _game_is_complete({"points": [{"score": "15 - 0"}, {"score": "30 - 0"}]}) is False


class TestSetDetection:
    def test_set_from_status(self):
        assert _current_set({"event_status": "Set 3"}) == 3
        assert _current_set({"event_status": "Set 1"}) == 1

    def test_set_from_scores_list(self):
        event = {
            "event_status": "In Progress",
            "event_live": "1",
            "scores": [
                {"score_first": "6", "score_second": "4", "score_set": "1"},
                {"score_first": "3", "score_second": "6", "score_set": "2"},
            ],
        }
        assert _current_set(event) == 3  # 2 completed sets + 1 in progress

    def test_set_from_scores_dict(self):
        event = {
            "event_status": "In Progress",
            "scores": {
                "1": {"score_first": "6", "score_second": "4"},
                "2": {"score_first": "3", "score_second": "2"},
                "game": {"score_first": "30", "score_second": "15"},
            },
        }
        assert _current_set(event) == 2


class TestSPWFromPBP:
    def test_basic_extraction(self):
        pbp = [{
            "set_number": "Set 1",
            "games": [
                {
                    "player_served": "First Player",
                    "serve_winner": "First Player",
                    "points": [
                        {"score": "15 - 0"}, {"score": "30 - 0"},
                        {"score": "40 - 0"}, {"score": "game"},
                    ],
                },
                {
                    "player_served": "Second Player",
                    "serve_winner": "Second Player",
                    "points": [
                        {"score": "0 - 15"}, {"score": "0 - 30"},
                        {"score": "0 - 40"}, {"score": "game"},
                    ],
                },
            ] * 5,  # repeat to get >= 10 points per server
        }]
        spw_first, spw_second = _extract_spw_from_pbp(pbp)
        assert spw_first > 0.5
        assert spw_second > 0.5

    def test_defaults_without_data(self):
        spw_h, spw_a = _extract_spw_from_pbp([])
        assert spw_h == 0.62
        assert spw_a == 0.62

    def test_handles_none(self):
        spw_h, spw_a = _extract_spw_from_pbp(None)
        assert spw_h == 0.62


class TestSurfaceDetection:
    def test_wimbledon_is_grass(self):
        assert _detect_surface({"league_name": "ATP - Wimbledon"}) == "grass"

    def test_roland_garros_is_clay(self):
        assert _detect_surface({"league_name": "ATP - Roland Garros"}) == "clay"

    def test_tournament_name_fallback(self):
        assert _detect_surface({"tournament_name": "ATP Madrid"}) == "clay"

    def test_unknown_defaults_hard(self):
        assert _detect_surface({"league_name": "ATP - US Open"}) == "hard"
