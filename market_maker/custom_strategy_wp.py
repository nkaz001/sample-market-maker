import sys

import pandas as pd

from market_maker.market_maker import OrderManager


class CustomOrderManager(OrderManager):
    """A sample order manager for implementing your own custom strategy"""

    def place_orders(self) -> None:
        order_qty = 100
        threshold = 0.10407176816108477

        ticker = self.get_ticker()
        market_depth = self.exchange.get_market_depth()
        bid = map(lambda x: (x['price'], x['size']), sorted(filter(lambda x: x['side'] == 'Buy', market_depth), key=lambda x: -x['price']))
        ask = map(lambda x: (x['price'], x['size']), sorted(filter(lambda x: x['side'] == 'Sell', market_depth), key=lambda x: x['price']))
        bid = pd.DataFrame(bid, columns=['price', 'size'])
        bid = bid[bid['size'].cumsum() <= 50000000]
        ask = pd.DataFrame(ask, columns=['price', 'size'])
        ask = ask[ask['size'].cumsum() <= 50000000]
        weighted_price = ((bid['price'] * bid['size']).sum() + (ask['price'] * ask['size']).sum()) / (bid['size'].sum() + ask['size'].sum())
        alpha = weighted_price - ticker['last']

        buy_orders = []
        sell_orders = []

        if alpha > threshold and not self.long_position_limit_exceeded():
            new_bid_price = ticker['last'] - self.instrument['tickSize']
            buy_orders.append({'price': new_bid_price, 'orderQty': order_qty, 'side': "Buy"})
        if alpha < -threshold and not self.short_position_limit_exceeded():
            new_ask_price = ticker['last'] + self.instrument['tickSize']
            sell_orders.append({'price': new_ask_price, 'orderQty': order_qty, 'side': "Sell"})

        self.converge_orders(buy_orders, sell_orders)


def run() -> None:
    order_manager = CustomOrderManager()

    # Try/except just keeps ctrl-c from printing an ugly stacktrace
    try:
        order_manager.run_loop()
    except (KeyboardInterrupt, SystemExit):
        sys.exit()
