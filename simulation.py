"""Deterministic, testable inventory replenishment game logic."""

from dataclasses import dataclass, field
from random import Random
from typing import Literal


@dataclass(frozen=True)
class Product:
    name: str
    max_demand: int

    @property
    def average_demand(self) -> float:
        # For a discrete uniform random variable from 0 to max_demand.
        return self.max_demand / 2


CATALOG = (
    Product("礦泉水", 3),
    Product("泡麵", 4),
    Product("牛奶", 5),
    Product("麵包", 2),
    Product("衛生紙", 4),
    Product("餅乾", 3),
    Product("咖啡", 5),
    Product("洗衣精", 2),
)


@dataclass(frozen=True)
class DailyResult:
    day: int
    choice: int
    stock_before: tuple[int, ...]
    stock_after_restock: tuple[int, ...]
    demand: tuple[int, ...]
    sold: tuple[int, ...]
    lost: tuple[int, ...]
    stock_end: tuple[int, ...]

    @property
    def total_demand(self) -> int:
        return sum(self.demand)

    @property
    def total_sold(self) -> int:
        return sum(self.sold)

    @property
    def total_lost(self) -> int:
        return sum(self.lost)


@dataclass
class InventoryGame:
    products: tuple[Product, ...]
    schedule: tuple[tuple[int, ...], ...]
    starting_units: int = 5
    restock_units: int = 10
    stock: list[int] = field(init=False)
    history: list[DailyResult] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        if not self.products or not self.schedule:
            raise ValueError("Products and schedule must be nonempty.")
        if any(len(day) != len(self.products) for day in self.schedule):
            raise ValueError("Every day must contain demand for each product.")
        if self.starting_units < 0 or self.restock_units <= 0:
            raise ValueError("Stock cannot be negative; restock must be positive.")
        if any(x < 0 for day in self.schedule for x in day):
            raise ValueError("Demand cannot be negative.")
        self.stock = [self.starting_units] * len(self.products)

    @property
    def day(self) -> int:
        return len(self.history)

    @property
    def days(self) -> int:
        return len(self.schedule)

    @property
    def finished(self) -> bool:
        return self.day >= self.days

    @property
    def total_sold(self) -> int:
        return sum(result.total_sold for result in self.history)

    @property
    def total_lost(self) -> int:
        return sum(result.total_lost for result in self.history)

    @property
    def total_demand(self) -> int:
        return self.total_sold + self.total_lost

    @property
    def service_rate(self) -> float:
        return self.total_sold / self.total_demand if self.total_demand else 1.0

    def step(self, choice: int) -> DailyResult:
        if self.finished:
            raise ValueError("The game has already ended.")
        if not isinstance(choice, int) or isinstance(choice, bool) or not 0 <= choice < len(self.products):
            raise ValueError("Invalid product index.")

        before = tuple(self.stock)
        restocked = self.stock.copy()
        restocked[choice] += self.restock_units
        demand = self.schedule[self.day]
        sold = tuple(min(available, required) for available, required in zip(restocked, demand))
        lost = tuple(required - actual for required, actual in zip(demand, sold))
        end = tuple(available - actual for available, actual in zip(restocked, sold))
        result = DailyResult(
            day=self.day + 1,
            choice=choice,
            stock_before=before,
            stock_after_restock=tuple(restocked),
            demand=demand,
            sold=sold,
            lost=lost,
            stock_end=end,
        )
        self.stock = list(end)
        self.history.append(result)
        return result


def new_game(n: int = 5, days: int = 14, seed: int = 2026) -> InventoryGame:
    if not 1 <= n <= len(CATALOG):
        raise ValueError("Invalid product count.")
    if days < 1:
        raise ValueError("Days must be positive.")
    if not isinstance(seed, int):
        raise ValueError("Seed must be an integer.")
    rng = Random(seed)
    products = CATALOG[:n]
    schedule = tuple(
        tuple(rng.randint(0, item.max_demand) for item in products)
        for _ in range(days)
    )
    return InventoryGame(products=products, schedule=schedule)


Policy = Literal["lowest_stock", "shortest_cover"]


def choose_by_policy(game: InventoryGame, policy: Policy) -> int:
    """Both policies use only known stock and disclosed demand ranges."""
    if policy == "lowest_stock":
        return min(
            range(len(game.products)),
            key=lambda i: (game.stock[i], -game.products[i].average_demand, i),
        )
    if policy == "shortest_cover":
        return min(
            range(len(game.products)),
            key=lambda i: (
                game.stock[i] / max(game.products[i].average_demand, 1e-9),
                -game.products[i].average_demand,
                i,
            ),
        )
    raise ValueError("Unknown policy.")


def run_baseline(source: InventoryGame, policy: Policy) -> InventoryGame:
    """Play against the exact same future demand, without reading it to decide."""
    replay = InventoryGame(
        products=source.products,
        schedule=source.schedule,
        starting_units=source.starting_units,
        restock_units=source.restock_units,
    )
    while not replay.finished:
        replay.step(choose_by_policy(replay, policy))
    return replay
