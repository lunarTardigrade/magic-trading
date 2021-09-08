import requests
import json
import os
import json
import time
import datetime
import math
import smtplib, ssl
import sys
import logging
from ratelimit import limits, sleep_and_retry

logging.basicConfig(filename='check.log', filemode='a', format='%(asctime)s - %(message)s')
logger=logging.getLogger()
logger.setLevel(logging.INFO)
og_stdout = sys.stdout
api_url_vwma = 'https://api.taapi.io/vwma'
api_url_ma = 'https://api.taapi.io/sma'
api_url_candle = 'https://api.taapi.io/candle'
periods = ['3d','1d','12h','4h','6h','8h','2h','1h','30m','15m']
allperiods = ['1m','3m','5m','15m','30m','1h','2h','4h','6h','8h','12h','1d','3d','1w','1M']
queue = []
triggers = []
i=0
allState = {}

def get_config(type):
    with open("config.json","r") as f:
        config = json.load(f)
    return config[type]
    #symbols = config["symbols"]
    #secret = config["secret"]
    #emails = config["emails"]
    #sender_email = config["sender_email"]
    #password = config["password"]

def fakeTrigger():
    if (len(queue) == 0):
        queue.append(('FAKE','15m'))
        work_queue(True)

def now():
    return datetime.datetime.now()

@sleep_and_retry
@limits(calls=5,period=15)
def get_vwma (symbol,interval,session,secret):
    params = '?secret=' + secret + '&exchange=binance&symbol=' + symbol + '&interval=' + interval + '&period=60&backtracks=5'
    _url= api_url_vwma +  params
    gotvwma= False
    attempt=0
    while not gotvwma:
        vwma = session.get(_url)
        attempt = attempt+1
        if vwma.status_code !=200:
            if attempt <5:
                logger.info("ERROR: " + str(vwma) + ", trying again")
                time.sleep(5)
            else:
                logger.info("ERROR: " + str(vwma) + ", max attempts reached")
                gotvwma=True
        else:
            gotvwma=True
    vwma_json = vwma.json()
    return vwma_json

@sleep_and_retry
@limits(calls=5,period=15)
def get_ma (symbol, interval,session,secret):
    params = '?secret=' + secret + '&exchange=binance&symbol=' + symbol + '&interval=' + interval + '&optInTimePeriod=60&backtracks=5'
    _url= api_url_ma + params
    gotma = False
    attempt = 0
    while not gotma:
        ma = session.get(_url)
        attempt = attempt+1
        if ma.status_code !=200:
            if attempt<5:
                logger.info("ERROR:" + str(ma) + ", trying again")
                time.sleep(5)
            else:
                logger.info("ERROR: " + str(ma) + ", max attempts reached")
                gotma=True
        else:
            gotma=True
    ma_json = ma.json()
    return ma_json

@sleep_and_retry
@limits(calls=5,period=15)
def get_last_1_min_candle (symbol,session,secret):
    params = '?secret=' + secret + '&exchange=binance&symbol=' + symbol + '&interval=1m&period=60'
    _url= api_url_candle + params
    gotcandle= False
    attempt = 0
    while not gotcandle:
        candle = session.get(_url)
        attempt = attempt +1
        if candle.status_code !=200:
            if attempt<5:
                logger.info("ERROR:" + str(candle) + ", trying again")
                time.sleep(5)
            else:
                logger.info("ERROR: " + str(candle) + ", max attempts reached")
                gotcandle=True
        else:
            gotcandle = True
    candle_json = candle.json()
    return candle_json

@sleep_and_retry
@limits(calls=5,period=15)
def check_for_state_change (symbol, interval,session,secret):
    vwma_list = []
    ma_list = []
    state_list = []
    print(str(now()) + "  getting last 5 vwma...")
    vwma = get_vwma (symbol, interval, session, secret)
    #print(vwma)
    print(str(now()) + "  getting last 5 ma...")
    ma = get_ma (symbol, interval, session, secret)
    for item in vwma:
        vwma_list.append(item['value'])
    for item in ma:
        ma_list.append(item['value'])
    vwma_list.pop(0)
    ma_list.pop(0)
    for i in range(4):
        #print("vwma " + str(i) + ": " + str(vwma_list[i]))
        #print("ma " + str(i) + ": " + str(ma_list[i]))
        if (vwma_list[i] > ma_list[i]):
            state_list.append("g")
        else: 
            state_list.append("r")
    if (state_list == ["r","r","g","g"]):
        state_change = "r"
        limit = ma_list[0]
    elif (state_list == ["g","g","r","r"]):
        state_change = "g"
        limit = vwma_list[0]
    else:
        state_change = "no"
        limit = ""
    print (str(now()) + "  last states are: " + str(state_list) )
    print (str(now()) + "  state_change: " + state_change)
    return state_change, limit

@sleep_and_retry
@limits(calls=5,period=15)
def check_for_trigger (symbol,interval,session,secret):
    price = ""
    trigger = "none"
    state_change, limit = check_for_state_change (symbol, interval,session,secret)
    if (state_change != "no"):
        print (str(now()) + "  limit: " + str(limit))
        print (str(now()) + "  getting price...")
        candle = get_last_1_min_candle (symbol, session,secret)
        price = candle['close']
        if (state_change == "g"):
            if (price<limit):
                trigger = "BUY"
        elif (state_change == "r"):
            if (price>limit):
                trigger = "SELL"
        print (str(now()) + "  last price: " + str(price))
        print (str(now()) + "  trigger: " + trigger) 
    return trigger, limit, price

def add_to_queue (interval):
    symbols = get_config("symbols")
    for each in symbols:
        queue.append((each,interval))

def getSession():
    session = requests.Session()
    return session

@sleep_and_retry
@limits(calls=5,period=15)
def work_queue(fake= False):
    session = getSession()
    triggerCount = 0
    print("-----")
    print("queue:")
    print(queue)
    print("-----")
    logger.info("Checks for this period: " + str(queue))
    while len(queue)>0:
        symbol,interval = queue[0]
        print (str(now()) + " checking " + symbol + " " + interval)
        if (fake):
            trigger = "BUY"
            limit = 123
            price =120
        else:
            secret = get_config("secret")
            trigger, limit, price = check_for_trigger (symbol,interval,session,secret)
        if (trigger != "none"):
            triggerCount = triggerCount + 1
            if (fake):
                confidence,count = 17,28
            else:
                confidence,count = GetConfidence(symbol, session,secret)
            if (trigger == "SELL"):
                confidence = count - confidence
            confidence = str(confidence) + "/" + str(count)
            triggers.append({'time': str(now()),'symbol' : symbol, 'interval' : interval, 'trigger' : trigger, 'price' : price, 'limit' : limit, 'confidence' : confidence})
            logger.info("New Trigger: " + str(triggers[len(triggers)-1]))
            with open ("trigger.txt","a") as f:
                sys.stdout = f
                print (triggers[len(triggers)-1])
                sys.stdout = og_stdout
            print(trigger + " " + symbol + " limit " + str(limit) + " triggered on " + interval + ". Confidence: " + confidence)
            send_email(trigger,symbol,limit,interval,price,confidence)
        queue.pop(0)
    print(str(now()) + " queue is now empty. ")
    print("New Triggers: " + str(triggerCount))
    if (len(triggers)>0):
        print("Triggers Found:")
    else:
        logger.info("No new triggers")
    for each in triggers:
        print(each)

def queue_all_checks():
    add_to_queue('3d')
    add_to_queue("1d")
    queue_midDay_checks()

def queue_midDay_checks():
    add_to_queue("12h")
    queue_eightHour_check()    

def queue_thirtyMin_checks():
    add_to_queue("30m")
    add_to_queue("15m")

def queue_oneHour_checks():
    add_to_queue("1h")
    queue_thirtyMin_checks()

def queue_twoHour_checks():
    add_to_queue("2h")
    queue_oneHour_checks()

def queue_fourHour_checks():
    add_to_queue("4h")
    queue_twoHour_checks()

def queue_sixHour_checks():
    add_to_queue("6h")
    queue_twoHour_checks()

def queue_eightHour_check():
    add_to_queue("8h")
    queue_fourHour_checks()

def pick_and_queue():
    hour = now().hour
    minute = now().minute
    if (hour==17 and minute<15):
        queue_all_checks()
    elif (hour==5 and minute<15):
        queue_midDay_checks()
    elif (hour in [1,9,] and minute<15):
        queue_eightHour_check()
    elif (hour in [23,11] and minute<15):
        queue_sixHour_checks()
    elif (hour in [21,13] and minute<15):
        queue_fourHour_checks()
    elif (hour in [3,7,15,19] and minute<15):
        queue_twoHour_checks()
    elif (minute<15):
        queue_oneHour_checks()
    elif (minute<30):
        add_to_queue("15m")
    elif (minute<45):
        queue_thirtyMin_checks()
    else:
        add_to_queue("15m")

def send_email(trigger,symble, limit, interval, price,confidence):
    port = 465
    sender_email = get_config("sender_email")
    password = get_config("password")
    context = ssl.create_default_context()
    content  = "Subject: "+ trigger + " " + symble + "("  + interval + ") | limit: " + str(limit) + " | last price: " + str(price) + " | confidence:" + confidence + " | " + str(now().strftime("%b %d %Y %H:%M:%S"))
    with smtplib.SMTP_SSL("smtp.gmail.com",port,context=context) as server:
        server.set_debuglevel(1)
        server.login(sender_email, password)
        emails = get_config("emails")
        for each in emails:
            server.sendmail(sender_email, each, content)

def quarterly_scan():
    logger.info("Scan Started")
    pick_and_queue()
    work_queue()
    logger.info("Scan Finished")

@sleep_and_retry
@limits(calls=5,period=15)
def GetConfidence(symbol,session,secret):
    getAllCurrentStates(symbol,session,secret)
    confidence = 0
    stateCount = 2*len(allState)
    for interval in allState:
        if (allState[interval]["vwmaState"] == "g"):
            confidence = confidence +1
        if (allState[interval]["overUnder"] == "u"):
            confidence = confidence +1            
    return confidence, stateCount

@sleep_and_retry
@limits(calls=5,period=15)
def getAllCurrentStates(symbol,session,secret):
    states = {}
    candle = get_last_1_min_candle (symbol, session,secret)
    price = float(candle['close'])
    #print ("Price: " + str(price))
    for interval in allperiods:
        #print("Interval: " + str(interval))
        overUnder = "o"
        vwmaState = "r"
        try:
            vwma = float(get_vwma(symbol, interval, session,secret)[0]["value"])
            #print ("     VWMA: " + str(vwma))
            ma = float(get_ma(symbol, interval, session,secret)[0]["value"])
            #print ("     MA: " + str(ma))
            allState[interval] = {}
            if (vwma > ma):
                vwmaState = "g"
            if (price < vwma):
                overUnder = "u"
            #print ("     VWMA State: " + str(vwmaState))
            #print ("     Over Under: " + str(overUnder))
            allState[interval]['vwmaState'] = vwmaState
            allState[interval]['overUnder'] = overUnder
        except:
            pass

quarterly_scan()
