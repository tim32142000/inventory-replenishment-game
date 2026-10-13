import pytest

from simulation import InventoryGame, Product, new_game, run_baseline, choose_by_policy


def test_step_replenishes_only_selected_product_and_calculates_lost_sales():
    game = InventoryGame(
        products=(Product("A", 10), Product("B", 10)),
        schedule=((16, 8),),
        starting_units=5,
        restock_units=10,
    )
    outcome = game.step(0)
    assert outcome.stock_before == (5, 5)
    assert outcome.stock_after_restock == (15, 5)
    assert outcome.sold == (15, 5)
    assert outcome.lost == (1, 3)
    assert game.stock == [0, 0]
    assert game.total_sold + game.total_lost == game.total_demand == 24
    assert game.service_rate == 20 / 24


def test_schedule_stays_equal_for_same_seed_regardless_of_player_choices():
    left = new_game(n=5, days=14, seed=42)
    right = new_game(n=5, days=14, seed=42)
    assert left.schedule == right.schedule
    for i in range(14):
        assert left.step(i % 5).demand == right.step((i + 1) % 5).demand


def test_inventory_never_goes_negative():
    game = new_game(n=8, days=30, seed=7)
    while not game.finished:
        result = game.step(0)
        assert all(stock >= 0 for stock in result.stock_end)
        assert result.total_sold + result.total_lost == result.total_demand


def test_finished_game_rejects_extra_restock():
    game = new_game(n=1, days=1, seed=3)
    game.step(0)
    with pytest.raises(ValueError, match="ended"):
        game.step(0)


@pytest.mark.parametrize("choice", [-1, 2, True, 1.5, "0"])
def test_invalid_product_choice_is_rejected(choice):
    game = new_game(n=2, days=1)
    with pytest.raises(ValueError, match="Invalid"):
        game.step(choice)


def test_baseline_replays_same_schedule_without_changing_player_game():
    game = new_game(n=5, days=7, seed=12)
    game.step(0)
    baseline = run_baseline(game, "shortest_cover")
    assert baseline.schedule == game.schedule
    assert baseline.day == 7
    assert game.day == 1
    assert baseline.total_sold + baseline.total_lost == sum(map(sum, game.schedule))


def test_lowest_stock_policy():
    game = InventoryGame(
        products=(Product("A", 2), Product("B", 6)),
        schedule=((0, 0),),
    )
    game.stock = [2, 3]
    assert choose_by_policy(game, "lowest_stock") == 0
    assert choose_by_policy(game, "shortest_cover") == 1


def test_zero_demand_service_rate_is_defined():
    game = InventoryGame(products=(Product("A", 0),), schedule=((0,),))
    game.step(0)
    assert game.service_rate == 1.0
    assert game.total_lost == 0


def test_invalid_game_parameters():
    with pytest.raises(ValueError):
        new_game(n=9)
    with pytest.raises(ValueError):
        new_game(days=0)
    with pytest.raises(ValueError):
        InventoryGame(products=(Product("A", 2),), schedule=((2, 3),))
