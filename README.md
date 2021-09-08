# magic-trading
 This script checks for BUY and SELL trading signals for a customizable selection of crypto assets for intervals 15 mins and larger.
 You must have a BASIC subscription to TAAPI.IO for this to work.
 Modify the config file to add your TAAPI.IO key, email address to recieve trading alerts, email address and password to send alerts from
 You can modify the symbols to include any pair available on binance
 Whenever you execute the script it will check only new candles published within that quarter hour... so if you want it always checking, set up a cron, or windows task, to execute the script every 15 mins.  (1 thing todo for sure; to figure out which candles to check, its looking at the system clock.  I assume the system clock is PST, because I was thinking this was just for me, but clearly there needs to be work to make this more flexable.)
