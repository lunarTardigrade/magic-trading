# magic-trading
 This script checks for BUY and SELL trading signals for a customizable selection of crypto assets for intervals 15 mins and larger.

You must have a BASIC subscription to TAAPI.IO for this to work.

Modify the config file to add your TAAPI.IO key, email address to recieve trading alerts, email address and password to send alerts from

You can modify the symbols to include any pair available on binance, but I would keep it to 10 at most 10 pairs because api calls are throttled so that only a basic subscription is needed... all api calls need to be done before the next 15 minute candle is published, so more than 10 assets will possibly push it over espessually for the end of day and midday checks.

Whenever you execute the script it will check only new candles published within that quarter hour... so if you want it always checking, set up a cron, or windows task, to execute the script every 15 mins.  (1 thing todo for sure; to figure out which candles to check, its looking at the system clock.  I assume the system clock is PST, because I was thinking this was just for me, but clearly there needs to be work to make this more flexable.)

I added a my historical triggers as of today 9.8.21.  Be sure to backtest a trading strategy before you start using these.  I don't want to be in the business of finincal advise ... so don't neccisarly do how I do... but how I do is average a very small percentage out 3-5% on Sell triggers, and Increment a small fixed amount I'm comfortably in on Buy triggers.  Historically this algorithm  produces clusters of Buy triggers... and then clusters of Sell triggers... so I average out, average out, average out, on the way up... taking profits, and then buying back, average in, average in, average in... on the way down for hopfully on average less than I sold it for.
