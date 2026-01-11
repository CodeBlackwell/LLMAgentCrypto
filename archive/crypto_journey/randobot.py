from lumibot.entities import Asset
from lumibot.backtesting import CcxtBacktesting
from lumibot.strategies.strategy import Strategy
from datetime import datetime
from colorama import Fore
import random
import sys


class MLTrader(Strategy):

    def initialize(self, cash_at_risk: float = 0.2, coin: str = "BTC", quote: str = "USDT"):
        self.set_market("24/7")
        self.sleeptime = "1D"
        self.last_trade = None
        self.cash_at_risk = cash_at_risk
        self.coin = coin
        self.quote = quote

    def position_sizing(self):
        cash = self.get_cash()
        last_price = self.get_last_price(
            Asset(symbol=self.coin, asset_type=Asset.AssetType.CRYPTO),
            quote=Asset(symbol=self.quote, asset_type="crypto"),
        )
        # Added this to handle missing prices
        if last_price == None:
            print(f"Warning: Could not get price for {self.coin}/{self.quote}")
            quantity = 0
        else:
            quantity = cash * self.cash_at_risk / last_price
        return cash, last_price, quantity

    def on_trading_iteration(self):
        cash, last_price, quantity = self.position_sizing()

        if last_price != None and quantity > 0:
            if cash > (quantity * last_price):
                choice = random.choice([0, 1, 2])

                if choice == 0:  # Hold
                    pass
                elif choice == 1:  # Buy
                    if self.last_trade == "sell":
                        self.sell_all()
                    order = self.create_order(
                        Asset(symbol=self.coin, asset_type=Asset.AssetType.CRYPTO),
                        quantity,
                        "buy",
                        type="market",
                        quote=Asset(symbol=self.quote, asset_type="crypto"),
                    )
                    print(Fore.LIGHTMAGENTA_EX + str(order) + Fore.RESET)
                    self.submit_order(order)
                    self.last_trade = "buy"
                elif choice == 2:  # Sell
                    if self.last_trade == "buy":
                        self.sell_all()
                    order = self.create_order(
                        Asset(symbol=self.coin, asset_type=Asset.AssetType.CRYPTO),
                        quantity,
                        "sell",
                        type="market",
                        quote=Asset(symbol=self.quote, asset_type="crypto"),
                    )
                    print(Fore.LIGHTMAGENTA_EX + str(order) + Fore.RESET)
                    self.submit_order(order)
                    self.last_trade = "sell"


if __name__ == "__main__":
    try:
        # Use a more recent timeframe for better data availability
        start_date = datetime(2023, 6, 1) 
        end_date = datetime(2023, 12, 31)
        exchange_id = "coinbase"
        kwargs = {
            "exchange_id": exchange_id,
        }
        CcxtBacktesting.MIN_TIMESTEP = "day"
        
        # Use BTC/USD which has good data availability on Coinbase
        coin = "BTC"
        quote = "USD"
        
        print(f"Running backtest for {coin}/{quote} on {exchange_id} from {start_date} to {end_date}")
        
        # Run without a benchmark to avoid errors
        results, strat_obj = MLTrader.run_backtest(
            CcxtBacktesting,
            start_date,
            end_date,
            benchmark_asset=None,  # No benchmark to avoid errors
            quote_asset=Asset(symbol=quote, asset_type="crypto"),
            parameters={"cash_at_risk": 0.25, "coin": coin, "quote": quote},
            **kwargs,
        )
    except Exception as e:
        print(f"Error during backtest: {str(e)}")
        sys.exit(1)
