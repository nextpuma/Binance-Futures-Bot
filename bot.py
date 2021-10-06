import json
import time
import bot_functions as bf
import config as cfg
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Connect to the binance api and produce a client
client = bf.init_client()

# Load settings from settings.json
settings = cfg.getBotSettings()
market = settings.market
leverage = int(settings.leverage)
margin_type = settings.margin_type
confirmation_periods = settings.trading_periods.split(",")
take_profit = float(settings.take_profit)
stop_loss = float(settings.stop_loss)

# turn off print unless we really need to print something
std = bf.getStdOut()
bf.blockPrint()
bf.singlePrint("Bot Started", std)

# global values used by bot to keep track of state
entry_price = 0
exit_price_trigger = 0
liquidation_price = 0
in_position = False
side = 0

# Initialise the market leverage and margin type.
bf.initialise_futures(client, _market=market, _leverage=leverage)
time.sleep(3)
while True:
    try:
        # if not currently in a position then execute this set of logic
        if not in_position:

            # generate signal data for the last 1000 candles
            entry = bf.get_multi_scale_signal(client, _market=market, _periods=confirmation_periods)
            # entry = 1

            # if the entry is -1, then open a SHORT
            if entry == -1:
                qty, side, in_position = bf.handle_signal(client, std,
                                                          market=market, leverage=leverage,
                                                          order_side="SELL", stop_side="BUY",
                                                          take_profit=take_profit, stop_loss=stop_loss)

            # if the entry is 1, then open a LONG
            elif entry == 1:
                qty, side, in_position = bf.handle_signal(client, std,
                                                          market=market, leverage=leverage,
                                                          order_side="BUY", stop_side="SELL",
                                                          take_profit=take_profit, stop_loss=stop_loss)
            else:
                bf.singlePrint("Conditions not matched, no trade will be taken", std)

        # If already in a position then check market and wait for the trade to complete
        elif in_position:
            position_active = bf.check_in_position(client, market)
            if not position_active:
                client.cancel_all_orders(market)
                bf.singlePrint("There is no open trade currently, checking to enter a new trade.", std)
                in_position = False
            else:
                bf.singlePrint(f"There is an open trade in progress for {market}. No new trade will be attempted.", std)

        time.sleep(10)
    except Exception as e:
        logger.error(str(e), exc_info=True)
        bf.singlePrint(f"Encountered Exception {e}", std)
        time.sleep(15)
