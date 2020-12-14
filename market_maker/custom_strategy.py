import sys

from market_maker.settings import settings
from market_maker.market_maker import OrderManager
from market_maker.utils import math


class CustomOrderManager(OrderManager):
    """A sample order manager for implementing your own custom strategy"""

    def place_orders(self) -> None:
        # https://github.com/nkaz001/market-maker-backtest

        order_qty = 100
        a = 0.030469681552729
        b = 0.5138382813864965
        half_spread = 0.0003191754083323428

        ticker = self.get_ticker()
        fair_basis = self.exchange.get_instrument()['fairBasis']
        skew = self.running_qty / settings.MAX_POSITION * b * -1
        #quote_mid_price = ticker['mid'] + a * fair_basis + skew
        quote_mid_price = ticker['last'] + a * fair_basis + skew
        new_bid_price = min(quote_mid_price * (1 - half_spread), ticker['last'] - self.instrument['tickSize'])
        new_ask_price = max(quote_mid_price * (1 + half_spread), ticker['last'] + self.instrument['tickSize'])

        new_bid_price = math.toNearest(new_bid_price, self.instrument['tickSize'])
        new_ask_price = math.toNearest(new_ask_price, self.instrument['tickSize'])

        buy_orders = []
        sell_orders = []

        if not self.long_position_limit_exceeded():
            buy_orders.append({'price': new_bid_price, 'orderQty': order_qty, 'side': "Buy"})
        if not self.short_position_limit_exceeded():
            sell_orders.append({'price': new_ask_price, 'orderQty': order_qty, 'side': "Sell"})

        self.converge_orders(buy_orders, sell_orders)


def run() -> None:
    order_manager = CustomOrderManager()

    # Try/except just keeps ctrl-c from printing an ugly stacktrace
    try:
        order_manager.run_loop()
    except (KeyboardInterrupt, SystemExit):
        sys.exit()
