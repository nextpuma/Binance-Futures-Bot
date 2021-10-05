import json
import time
import bot_functions as bf
import config as cfg
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

#Connect to the binance api and produce a client
client = bf.init_client()

#Load settings from settings.json
settings = cfg.getBotSettings()
market = settings.market
leverage = int(settings.leverage)
margin_type = settings.margin_type
confirmation_periods = settings.trading_periods.split(",")
take_profit = float(settings.take_profit)
stop_loss = float(settings.stop_loss)
# trailing_percentage = float(settings.trailing_percentage)

#turn off print unless we really need to print something
std = bf.getStdOut()
bf.blockPrint()
bf.singlePrint("Bot Starting", std)

#global values used by bot to keep track of state
entry_price = 0
exit_price_trigger = 0
liquidation_price = 0
in_position = False
side = 0

#Initialise the market leverage and margin type.
bf.initialise_futures(client, _market=market, _leverage=leverage)

while True:
    try:
        #if not currently in a position then execute this set of logic
        if in_position == False:

            #generate signal data for the last 500 candles
            entry = bf.get_multi_scale_signal(client, _market=market, _periods=confirmation_periods)
            # entry = 1

            #if the second last signal in the generated set of data is -1, then open a SHORT
            if entry == -1:
                qty, side, in_position = bf.handle_signal(client, std, 
                                                          market=market, leverage=leverage, 
                                                          order_side="SELL", stop_side="BUY", 
                                                          _take_profit=take_profit, _stop_loss=stop_loss)

            #if the second last signal in the generated set of data is 1, then open a LONG
            elif entry == 1:
                qty, side, in_position = bf.handle_signal(client, std, 
                                                          market=market, leverage=leverage, 
                                                          order_side="BUY", stop_side="SELL",
                                                          _take_profit=take_profit, _stop_loss=stop_loss)

        #If already in a position then check market and decide when to exit
        elif in_position == True:
            position_active = bf.check_in_position(client, market)
            if position_active == False:
                bf.singlePrint("There are no open trades currently. Checking to enter a new trade.", std)
            else:
                bf.singlePrint(f"There is an open trade in progress for {market}. No new trade will be attempted.", std)
           
            # #generate signal data for the last 500 candles
            # entry = bf.get_multi_scale_signal(client, _market=market, _periods=confirmation_periods)
            #
            # #get the last market price
            # market_price = bf.get_market_price(client, _market=market)
            #
            # #if we generated a signal that is the opposite side of what our position currently is
            # #then sell our position. The bot will open a new position on the opposite side when it loops back around!
            # if entry != side:
            #     bf.singlePrint("Exit", std)
            #
            #     bf.close_position(client, _market=market)
            #
            #     #close any open trailing stops we have
            #     client.cancel_all_orders(market)
            #     time.sleep(3)
            #
            #     bf.singlePrint(f"Exited Position: {qty} ${market_price}", std)
            #
            #     bf.log_trade(_qty=qty, _market=market, _leverage=leverage, _side=side,
            #                   _cause="Signal Change", _market_price=market_price,
            #                   _type="EXIT")
            #
            #     in_position = False
            #     side = 0
            #
            # position_active = bf.check_in_position(client, market)
            # if position_active == False:
            #
            #     bf.log_trade(_qty=qty, _market=market, _leverage=leverage, _side=side,
            #       _cause="Signal Change", _market_price=market_price,
            #       _type="Trailing Stop")
            #     in_position = False
            #     side = 0
            #
            #     bf.singlePrint(f"Trailing Stop Triggered: {qty} ${market_price}", std)
            #
            #     #close any open trailing stops we have one
            #     client.cancel_all_orders(market)
            #     time.sleep(3)

        time.sleep(15)
    except Exception as e:
        logger.error(str(e), exc_info=True)
        bf.singlePrint(f"Encountered Exception {e}", std)
        time.sleep(15)
