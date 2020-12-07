import sys

from market_maker.settings import settings
from market_maker.market_maker import OrderManager
from market_maker.utils import math


class CustomOrderManager(OrderManager):
    """A sample order manager for implementing your own custom strategy"""

    def place_orders(self) -> None:
        # https://blog.bitmex.com/how-to-market-make-bitcoin-derivatives-lesson-2
        #
        # Quote Mid Price = Spot Price + Basis + Skew
        # Skew = (Change in Position / Total Size Quoted) * Weighted Average Half Spread * -1
        #
        # To simplify, quote fixed quantity on each side.
        #
        # https://bitmex.com/app/fairPriceMarking
        #
        # funding basis = funding rate * (time until funding / funding interval)
        # fair price = spot price * (1 + funding basis)
        #
        # Quote Mid Price = Fair Price + Skew
        # New Bid Price = Quote Mid Price * (1 - Half Spread)
        # New Ask Price = Quote Mid Price * (1 + Half Spread)
        #
        # https://ieor.columbia.edu/files/seasdepts/industrial-engineering-operations-research/pdf-files/Borden_D_FESeminar_Sp10.pdf
        #
        # New Bid Price = Mid Price + A * forecast - B * MCR - Half Spread
        # New Ask Price = Mid Price + A * forecast - B * MCR + Half Spread
        # MCR = running_qty / max_position * volatility

        ticker = self.get_ticker()
        fair_basis = self.exchange.get_instrument()['fairBasis']
        half_spread = 0.0005
        volatility = 0.1
        order_qty = 100
        a = 1
        b = 100 * half_spread
        skew = self.running_qty / settings.MAX_POSITION * volatility * b * -1
        quote_mid_price = ticker['mid'] + a * fair_basis + skew
        new_bid_price = quote_mid_price * (1 - half_spread)
        new_ask_price = quote_mid_price * (1 + half_spread)

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
