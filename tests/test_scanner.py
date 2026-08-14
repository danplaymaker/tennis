"""Tests for the live scanner's API-Tennis parsing logic."""

from src.live.scanner import (
    _collapse_pbp_games,
    _current_set,
    _extract_spw_from_pbp,
    _extract_spw_from_stats,
    _game_had_deuce,
    _game_is_complete,
    _hold_margin,
    _is_tiebreak_entry,
    _detect_surface,
    _player_name,
)


class TestTiebreakDetection:
    def test_tb_label(self):
        assert _is_tiebreak_entry({"number_game": "TB"}) is True

    def test_tiebreak_label(self):
        assert _is_tiebreak_entry({"number_game": "Tie Break"}) is True

    def test_game_13(self):
        assert _is_tiebreak_entry({"number_game": "13"}) is True

    def test_normal_game(self):
        assert _is_tiebreak_entry({"number_game": "7"}) is False

    def test_missing_number(self):
        assert _is_tiebreak_entry({}) is False

    def test_tiebreak_from_point_scoring(self):
        entry = {"number_game": "13", "points": [
            {"score": "1 - 0"}, {"score": "1 - 1"}, {"score": "2 - 1"},
        ]}
        assert _is_tiebreak_entry(entry) is True

    def test_normal_scoring_not_tiebreak(self):
        entry = {"number_game": "5", "points": [
            {"score": "15 - 0"}, {"score": "30 - 0"}, {"score": "40 - 0"},
        ]}
        assert _is_tiebreak_entry(entry) is False


class TestCollapsePbpGames:
    def test_normal_games_stay_separate(self):
        pbp = [
            {"set_number": "Set 1", "number_game": "1", "player_served": "First",
             "serve_winner": "First", "points": [{"score": "15-0"}, {"score": "game"}]},
            {"set_number": "Set 1", "number_game": "2", "player_served": "Second",
             "serve_winner": "Second", "points": [{"score": "0-15"}, {"score": "game"}]},
        ]
        games = _collapse_pbp_games(pbp)
        assert len(games) == 2

    def test_tiebreak_points_collapsed(self):
        pbp = [
            {"set_number": "Set 1", "number_game": "1", "player_served": "First",
             "serve_winner": "First", "points": [{"score": "15-0"}, {"score": "game"}]},
        ]
        for i in range(16):
            pbp.append({
                "set_number": "Set 1", "number_game": "13",
                "player_served": "First",
                "points": [{"score": f"{i//2} - {i - i//2}"}],
            })
        pbp[-1]["serve_winner"] = "First"
        games = _collapse_pbp_games(pbp)
        assert len(games) == 2
        assert games[1][2] is True  # is_tiebreak

    def test_tiebreak_points_merged_into_single_entry(self):
        pbp = []
        for i in range(10):
            pbp.append({
                "set_number": "Set 1", "number_game": "TB",
                "player_served": "First",
                "points": [{"score": f"{i} - 0"}],
            })
        pbp[-1]["serve_winner"] = "First"
        games = _collapse_pbp_games(pbp)
        assert len(games) == 1
        assert len(games[0][1]["points"]) == 10
        assert games[0][2] is True


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
        assert _current_set(event) == 3

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


class TestSPWFromStats:
    def test_extracts_from_stat_array(self):
        stats = [
            {"player_key": "100", "stat_name": "Service Points Won", "stat_won": "45", "stat_total": "70", "stat_period": "all"},
            {"player_key": "200", "stat_name": "Service Points Won", "stat_won": "38", "stat_total": "65", "stat_period": "all"},
        ]
        spw_a, spw_b = _extract_spw_from_stats(stats, "100", "200")
        assert abs(spw_a - 45 / 70) < 0.001
        assert abs(spw_b - 38 / 65) < 0.001

    def test_defaults_without_data(self):
        assert _extract_spw_from_stats([], "1", "2") == (0.62, 0.62)

    def test_needs_minimum_points(self):
        stats = [
            {"player_key": "100", "stat_name": "Service Points Won", "stat_won": "3", "stat_total": "5", "stat_period": "all"},
        ]
        spw_a, _ = _extract_spw_from_stats(stats, "100", "200")
        assert spw_a == 0.62


class TestSPWFromPBP:
    def test_flat_game_list(self):
        """pbp is a flat list of game dicts, not nested sets."""
        pbp = [
            {
                "set_number": "Set 1", "number_game": "1",
                "player_served": "First Player", "serve_winner": "First Player",
                "points": [{"score": "15 - 0"}, {"score": "30 - 0"}, {"score": "40 - 0"}, {"score": "game"}],
            },
            {
                "set_number": "Set 1", "number_game": "2",
                "player_served": "Second Player", "serve_winner": "Second Player",
                "points": [{"score": "0 - 15"}, {"score": "0 - 30"}, {"score": "0 - 40"}, {"score": "game"}],
            },
        ] * 5  # repeat for >= 10 points per server
        spw_first, spw_second = _extract_spw_from_pbp(pbp)
        assert spw_first > 0.5
        assert spw_second > 0.5

    def test_defaults_without_data(self):
        assert _extract_spw_from_pbp([]) == (0.62, 0.62)

    def test_handles_none(self):
        assert _extract_spw_from_pbp(None) == (0.62, 0.62)


class TestSurfaceDetection:
    def test_wimbledon_is_grass(self):
        assert _detect_surface({"league_name": "ATP - Wimbledon"}) == "grass"
        assert _detect_surface({"tournament_name": "Wimbledon"}) == "grass"

    def test_roland_garros_is_clay(self):
        assert _detect_surface({"league_name": "ATP - Roland Garros"}) == "clay"

    def test_tournament_name_fallback(self):
        assert _detect_surface({"tournament_name": "ATP Madrid"}) == "clay"

    def test_unknown_defaults_hard(self):
        assert _detect_surface({"league_name": "ATP - US Open"}) == "hard"


class TestHoldMargin:
    def test_hold_to_love(self):
        game = {
            "serve_winner": "first",
            "points": [
                {"score": "15 - 0"}, {"score": "30 - 0"},
                {"score": "40 - 0"}, {"score": "game"},
            ],
        }
        margin, held = _hold_margin(game, is_first_server=True)
        assert margin == 0
        assert held is True

    def test_hold_to_15(self):
        game = {
            "serve_winner": "first",
            "points": [
                {"score": "15 - 0"}, {"score": "15 - 15"},
                {"score": "30 - 15"}, {"score": "40 - 15"}, {"score": "game"},
            ],
        }
        margin, held = _hold_margin(game, is_first_server=True)
        assert margin == 1
        assert held is True

    def test_hold_to_30(self):
        game = {
            "serve_winner": "first",
            "points": [
                {"score": "15 - 0"}, {"score": "15 - 15"},
                {"score": "15 - 30"}, {"score": "30 - 30"},
                {"score": "40 - 30"}, {"score": "game"},
            ],
        }
        margin, held = _hold_margin(game, is_first_server=True)
        assert margin == 2
        assert held is True

    def test_broken(self):
        game = {
            "serve_lost": "first",
            "points": [
                {"score": "0 - 15"}, {"score": "0 - 30"},
                {"score": "0 - 40"}, {"score": "game"},
            ],
        }
        margin, held = _hold_margin(game, is_first_server=True)
        assert margin == -1
        assert held is False

    def test_deuce_hold(self):
        game = {
            "serve_winner": "first",
            "points": [
                {"score": "15 - 0"}, {"score": "15 - 15"},
                {"score": "30 - 15"}, {"score": "30 - 30"},
                {"score": "40 - 30"}, {"score": "40 - 40"},
                {"score": "ad - 40"}, {"score": "game"},
            ],
        }
        margin, held = _hold_margin(game, is_first_server=True)
        assert margin == 4
        assert held is True

    def test_second_server_returner_is_left(self):
        game = {
            "serve_winner": "second",
            "points": [
                {"score": "15 - 0"}, {"score": "15 - 15"},
                {"score": "15 - 30"}, {"score": "15 - 40"}, {"score": "game"},
            ],
        }
        margin, held = _hold_margin(game, is_first_server=False)
        assert margin == 1
        assert held is True

    def test_no_points_unknown(self):
        game = {"serve_winner": "first"}
        margin, held = _hold_margin(game, is_first_server=True)
        assert margin == -99
