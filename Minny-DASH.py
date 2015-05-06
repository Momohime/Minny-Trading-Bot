import json
import requests
import warnings
import time
import re
import hmac
import hashlib
import urllib




#######################################################################################################
# CoinSwap has been removed because withdraw does not work and the transfer to GAW is shady/no support#
# All Code is still included except for wait method and balance                                       #
#                                                                                                     #
# UPDATE: CoinSwap has shut down on 3/22/15                                                           #
#######################################################################################################

global eqDRK
global checkTime

#Reads the cookie from the file so CoinSwap allows the connection. Got the technique from stackexchange =)
# def importcookies(filename='savedcookies.txt'):
#     f = open(filename, 'r')
#     return pickle.load(f)

# cookie = importcookies()

checkTime = None

#These variable can be changed depending on how much the all wallets should hold
eqDRK = 3
eqBTC = 0.05
waitWhile = 0.05

mainDash = eqDRK

#waitWhile is the BTC Amount that triggers the wait method to run. The reason eqBTC is not used is because the moment it goes
# below the eqBTC amount, Minny will wait for a refill even though there is still enough BTC to execute trades. This is a waste of time.
# So waitWhile is set to when Minny should start waiting. In this case it is set to (10 * current_XPY_Price)


amountToSell = 0

#Something in the Cryptsy code causes a urllib3 error to arise. This is just to prevent that error from printing
warnings.filterwarnings("ignore")

allbuy = {}
allsell = {}

#This is just here for reference. The variable is never used.
coinswapapikey = 'dsom0Wc2BjGxZOR9'

balances= {}

checkbalance = False

# paycoinwallet = ServiceProxy("http://tiny:yellowfin@127.0.0.1:8332")
# bitcoinwallet = ServiceProxy("http://bittiny:bityellowfin@127.0.0.1:9090")


#THIS TOOK FOREVER TO FIND HOW TO DO


#Cryptsy info
PrivKey = "Your Cryptsy Private Key Here"
PublKey = "Your Cryptsy Public Key Here"


profit = 0


#Bittrex info

BittrexKey = "Your Bittrex Key Here"
BittrexSecret = "Your Bittrex Secret Here"


needToRefillDash = {"Cryptsy":0,"Bittrex":0,"Poloniex":0}
needToRefillBtc = {"Cryptsy":0,"Bittrex":0,"Poloniex":0}


const = 1

#Poloniex Stuff

poloniexKey = "Your Poloniex Key Here"
poloniexSecret = "Your Poloniex Secret Here"
poloniexURL = "https://poloniex.com/tradingApi"

#Function to send a buy request to marketname
def buy(marketname, toBuy, lowSell):
    print "Buying...."

    if marketname == 'Cryptsy':
        query = {"method":"createorder", "marketid":155, "ordertype":"buy", "quantity":toBuy, "price":lowSell, "nonce":time.time()}
        
        encoded = urllib.urlencode(query)
        
        signature = hmac.new(PrivKey,encoded,hashlib.sha512).hexdigest()
        
        CryptsyHeader = {'Sign':signature, 'Key': PublKey}
        
        cryptsybuyorder = requests.post("https://api.cryptsy.com/api", data=query, headers=CryptsyHeader,timeout=15).json()

        print "Buy Time: " + str(time.time())
        if cryptsybuyorder['success'] == '1' or cryptsybuyorder['success'] == 1:
           print "Buy Order id from Cryptsy is:" + cryptsybuyorder['orderid']
           return True
        else:
           print "Cryptsy Buy Failed!!! ={"
           
           return False
    elif marketname == 'Bittrex':
        buyParam = {"market" : "BTC-DASH", "quantity" : toBuy, "rate" : lowSell}
        nonceBit = time.time()
        bittrexURL = "https://bittrex.com/api/v1.1/market/buylimit?" + "apikey=" + BittrexKey + "&" + "nonce=" + str(nonceBit) + "&"
        bittrexURL = bittrexURL + urllib.urlencode(buyParam)
            
        BittrexSign = hmac.new(BittrexSecret,bittrexURL,hashlib.sha512).hexdigest()
        bittrexHeader = {"apisign":BittrexSign}
        bittrexbuyorder = requests.get(bittrexURL,headers=bittrexHeader).json()
        print "Buy Time: " + str(time.time())

        if bittrexbuyorder['success'] == True:
            print "Buy Order from Bittrex is successful: " + bittrexbuyorder['result']['uuid']
            return True
        else:
            print "Bittrex Buy Failed!!! ={"
            return False


    elif marketname == 'Poloniex':
        nonce = time.time()
        buyParam = {"command":"buy", "currencyPair" : "BTC_DASH", "amount" : toBuy, "rate" : lowSell, "nonce" : nonce}
        post_data = urllib.urlencode(buyParam)
        sign = hmac.new(poloniexSecret, post_data, hashlib.sha512).hexdigest()
        PoloniexHeader = {"Key" : poloniexKey, "Sign" : sign}
        poloniexbuyorder = (requests.post(poloniexURL, data=buyParam, headers=PoloniexHeader)).json()

        for key in poloniexbuyorder.keys():
            if key == 'error':
                print "Poloniex Buy Failed! -- " + poloniexbuyorder['error']
                return False

        print "Poloniex Buy Order successful! : " + poloniexbuyorder['orderNumber']
        return True



#Function to send a sell request to marketname. If sell ever fails the marketname is changed to the name of the market where the
# buy occured. Then the highBuy is changed to the price the buy bought at. This way a sell is issued in the same market as the buy
# at the same price that it was bought at. (Crypsty fee is accounted for)
def sell(marketname, toSell, highBuy, boughtfromthismarket, lowSell):
    print "Selling..."

    if marketname == 'Cryptsy':
        query = {"method":"createorder", "marketid":155, "ordertype":"sell", "quantity":toSell, "price":highBuy, "nonce":time.time()}
        
        encoded = urllib.urlencode(query)
        
        signature = hmac.new(PrivKey,encoded,hashlib.sha512).hexdigest()
        
        CryptsyHeader = {'Sign':signature, 'Key': PublKey}
        
        cryptsysellorder = requests.post("https://api.cryptsy.com/api", data=query, headers=CryptsyHeader,timeout=15).json()
        

        print "Sell Time: " + str(time.time())
        if cryptsysellorder['success'] == '1' or cryptsysellorder['success'] == 1:
            print "Sell Order id from Cryptsy is:" + cryptsysellorder['orderid']
            return True
        else:
            print "Cryptsy Sell Failed!!! ={. I am selling back what I bought!"
            if boughtfromthismarket == 'Cryptsy':
                tip = 0.0024
            elif boughtfromthismarket == 'Bittrex':
                tip = 0.0025
            elif boughtfromthismarket == 'Poloniex':
                tip = 0.002

            ee = (((toSell * lowSell) + ((toSell * lowSell) * tip)))
            lowSell = ee/(toSell - (toSell * tip))
            sell(boughtfromthismarket, toSell, lowSell, boughtfromthismarket, lowSell)
            return False
    elif marketname == 'Bittrex':
        sellParam = {"market" : "BTC-DASH", "quantity" : toSell, "rate" : highBuy}
        nonceBit = time.time()
        bittrexURL = "https://bittrex.com/api/v1.1/market/selllimit?" + "apikey=" + BittrexKey + "&"  + "nonce=" + str(nonceBit) + "&"
        
        bittrexURL = bittrexURL + urllib.urlencode(sellParam)
        
        BittrexSign = hmac.new(BittrexSecret,bittrexURL,hashlib.sha512).hexdigest()
        bittrexHeader = {"apisign":BittrexSign}
        bittrexsellorder = requests.get(bittrexURL,headers=bittrexHeader).json()
        print "Sell Time: " + str(time.time())

        if bittrexsellorder['success'] == True:
            print "Sell Order from Bittrex is successful: " + bittrexsellorder['result']['uuid']
            return True
        else:
            print "Bittrex Sell Failed!!! ={. I am selling back what I bought!"
            if boughtfromthismarket == 'Cryptsy':
                tip = 0.0024
            elif boughtfromthismarket == 'Bittrex':
                tip = 0.0025
            elif boughtfromthismarket == 'Poloniex':
                tip = 0.002
            ee = (((toSell * lowSell) + ((toSell * lowSell) * tip)))
            lowSell = ee/(toSell - (toSell * tip))
            sell(boughtfromthismarket, toSell, lowSell, boughtfromthismarket, lowSell)
            return False

    elif marketname == 'Poloniex':
        nonce = time.time()
        buyParam = {"command":"sell", "currencyPair" : "BTC_DASH", "amount" : toSell, "rate" : highBuy, "nonce" : nonce}
        post_data = urllib.urlencode(buyParam)
        sign = hmac.new(poloniexSecret, post_data, hashlib.sha512).hexdigest()
        PoloniexHeader = {"Key" : poloniexKey, "Sign" : sign}
        poloniexbuyorder = (requests.post(poloniexURL, data=buyParam, headers=PoloniexHeader)).json()
        
        for key in poloniexbuyorder.keys():
            if key == 'error':
                
                print "Poloniex Buy Failed! -- " + poloniexbuyorder['error']
                
                if boughtfromthismarket == 'Cryptsy':
                    tip = 0.0024
                elif boughtfromthismarket == 'Bittrex':
                    tip = 0.0025
                elif boughtfromthismarket == 'Poloniex':
                    tip = 0.002
                
                ee = (((toSell * lowSell) + ((toSell * lowSell) * tip)))
                lowSell = ee/(toSell - (toSell * tip))
                sell(boughtfromthismarket, toSell, lowSell, boughtfromthismarket, lowSell)
                return False
    
        print "Poloniex Buy Order successful! : " + poloniexbuyorder['orderNumber']
        return True






#Function that returns the amount of XPY Minny can buy only based on the buyfrommarket (does not check selltomarket to make sure
# that Minny can sell just as much as she buys. This check is done later)
def amount(num, totalbuy):
        if totalbuy <= eqDRK and totalbuy <= num:
            return totalbuy
        elif totalbuy > num and num <= eqDRK:
            return num
        elif num > eqDRK and num > totalbuy and totalbuy <= eqDRK:
            return totalbuy
        else:
            return eqDRK


def restockDASH(btcMarket, dashAMT,dashMarket):
    txid = 'TMPT'
    addy = ""
    DASHFEE = 0
    
    print "Attempting to Refill DASH..."
    
    if dashMarket == 'Cryptsy':
        addy = 'XekzVcur7PdWPjEH6xzYCau8gkhNbb5tJH'
    elif dashMarket == 'Bittrex':
        addy = 'Xq57F3sjqu1nzzNSYEihsZp2F8Qw4RoPiz'
    elif dashMarket == 'Poloniex':
        addy = 'Xf7K3LToquu1Gozcno5q6ss43pz8oUdUr4'



    if btcMarket == 'Cryptsy':
        DASHFEE = 0.00400000
        query = {"method":"makewithdrawal", "address":addy, "amount":dashAMT + DASHFEE, "nonce":time.time()}
        
        encoded = urllib.urlencode(query)
        
        signature = hmac.new(PrivKey, encoded, hashlib.sha512).hexdigest()
        
        CryptsyHeader = {'Sign': signature, 'Key': PublKey}
        
        cryptsywithdrawal = requests.post("https://api.cryptsy.com/api",data=query,headers=CryptsyHeader)

        if cryptsywithdrawal.json()['success'] == '1' or cryptsywithdrawal['success'] == 1:
            print "Cryptsy DashCoin withdrawal successfull! - " + str(dashAMT) + " DASH " +  "Sent to: " + addy
            print "Let me wait 5 seconds to make sure withdrawal goes through =)"
            time.sleep(5)
            
            #Update balnces after restock
            getBalances()

            return True
        else:
            print "Cryptsy DashCoin withdrawal failed!"
            return False

    elif btcMarket == 'Bittrex':
        DASHFEE = 0.00200000
        bitParams = {"currency" : "DASH", "quantity": dashAMT + DASHFEE, "address" : addy}
        nonceBit = time.time()
        bittrexURL = "https://bittrex.com/api/v1.1/account/withdraw?" + "apikey=" + BittrexKey + "&" + "nonce=" + str(nonceBit) + "&"
        bittrexURL = bittrexURL + urllib.urlencode(bitParams)
        BittrexSign = hmac.new(BittrexSecret,bittrexURL,hashlib.sha512).hexdigest()
        bittrexHeader = {"apisign" : BittrexSign}
        bittrexwithdrawal = requests.get(bittrexURL,headers=bittrexHeader).json()

        if bittrexwithdrawal['success'] == True:
            print "Bittrex DashCoin withdrawal successful! - " + str(dashAMT) + " DASH " +  "Sent to: " + addy + " " + bittrexwithdrawal['result']['uuid']
            print "Let me wait 5 seconds to make sure withdrawal goes through =)"
            time.sleep(5)
            
            getBalances()

            return True

        else:
            print "Bittrex DashCoin withdrawal failed!"
            return False

    elif btcMarket == 'Poloniex':
        DASHFEE = 0.05
        nonce = time.time()
        poloParams = {"command" : "withdraw", "currency" : "DASH", "amount": dashAMT + DASHFEE, "address" : addy, "nonce" : nonce}
        post = urllib.urlencode(poloParams)
        sig = hmac.new(poloniexSecret, post, hashlib.sha512).hexdigest()
        PoloniexHeader = {"Key" : poloniexKey, "Sign" : sig}
        poloWithdraw = requests.post(poloniexURL, data=poloParams, headers=PoloniexHeader).json()

        for key in poloWithdraw.keys():
            if key == 'error':
                print "Poloniex Withdraw Failed! -- " + poloWithdraw['error']
                return False
        
        print "Poloniex Withdraw successful!"
        return True




def restockBTC(dashMarket,btcAMT,btcMarket):
    print "Attempting to refill BTC..."

    if btcMarket == 'Cryptsy':
        addy = '1BdNnDyxAHigoMxj2keekJhtY2v64aVYCq'
    elif btcMarket == 'Bittrex':
        addy = '1HnAVFRFYiV5LP1Fpjb24RxBRdU8gi8rcc'
    elif btcMarket == 'Poloniex':
        addy = '1P5Gv96vTga4qNXCtA7yN2fPH4r6rQPden'

    


    if dashMarket == 'Cryptsy':
        BTCFEE = 0.001
        query = {"method":"makewithdrawal", "address":addy, "amount":btcAMT + BTCFEE, "nonce":time.time()}
        
        encoded = urllib.urlencode(query)
        
        signature = hmac.new(PrivKey, encoded, hashlib.sha512).hexdigest()
        
        CryptsyHeader = {'Sign': signature, 'Key': PublKey}
        
        cryptsywithdrawal = requests.post("https://api.cryptsy.com/api",data=query,headers=CryptsyHeader)
        
        if cryptsywithdrawal.json()['success'] == '1' or cryptsywithdrawal['success'] == 1:
            print "Cryptsy BitCoin withdrawal successfull! - " + str(btcAMT) + " BTC " +  "Sent to: " + addy
            
            getBalances()
            
            return True
        else:
            print "Cryptsy BitCoin withdrawal failed!"
            return False

    elif dashMarket == 'Bittrex':
        BTCFEE = 0.0002
        bitParams = {"currency" : "BTC", "quantity": btcAMT + BTCFEE, "address" : addy}
        nonceBit = time.time()
        bittrexURL = "https://bittrex.com/api/v1.1/account/withdraw?" + "apikey=" + BittrexKey + "&" + "nonce=" + str(nonceBit) + "&"
        bittrexURL = bittrexURL + urllib.urlencode(bitParams)
        BittrexSign = hmac.new(BittrexSecret,bittrexURL,hashlib.sha512).hexdigest()
        bittrexHeader = {"apisign" : BittrexSign}
        bittrexwithdrawal = requests.get(bittrexURL,headers=bittrexHeader).json()
        
        if bittrexwithdrawal['success'] == True:
            print "Bittrex BitCoin withdrawal successful! - " + str(btcAMT) + " BTC " +  "Sent to: " + addy + " " + bittrexwithdrawal['result']['uuid']
            
            getBalances()
            
            return True
        
        else:
            print "Bittrex BitCoin withdrawal failed!"
            return False

    elif dashMarket == 'Poloniex':
        BTCFEE = 0.0001
        nonce = time.time()
        poloParams = {"command" : "withdraw", "currency" : "BTC", "amount": btcAMT + BTCFEE, "address" : addy, "nonce" : nonce}
        post = urllib.urlencode(poloParams)
        sig = hmac.new(poloniexSecret, post, hashlib.sha512).hexdigest()
        PoloniexHeader = {"Key" : poloniexKey, "Sign" : sig}
        poloWithdraw = requests.post(poloniexURL, data=poloParams, headers=PoloniexHeader).json()
        
        for key in poloWithdraw.keys():
            if key == 'error':
                print "Poloniex Withdraw Failed! -- " + poloWithdraw['error']
                return False
        
        print "Poloniex Buy Order successful! : " + poloniexbuyorder['orderNumber']
        return True







#Function that returns all balances in all markets in a dict {nameOfMarket : [BTCamount, XPYamount]}

#####
#If this method keeps printing "Something went wrong when I was checking the balances. Let me try again in 30 seconds" then CoinSwap balance is probably zero in either BTC or XPY
#####
def getBalances():
        global balances
        print "Checking Balances"
        try:
          query = {"method":"getinfo", "nonce":time.time()}
                
          encoded = urllib.urlencode(query)
                    
          signature = hmac.new(PrivKey, encoded, hashlib.sha512).hexdigest()
                        
          CryptsyHeader = {'Sign': signature, 'Key': PublKey}
                            
          cryptsybalances = requests.post("https://api.cryptsy.com/api",data=query,headers=CryptsyHeader,timeout=10).json()
                                
          if cryptsybalances['success'] != '1':
                print "Something went wrong when I was checking the balances. Let me try again in 30 seconds"
                time.sleep(30)
                return getBalances()

          #need nonce and signature
          #Some notes. bittrexURL has to be EXACTLY the same as bittrexbalances.url. (params=xxxx) will change the order
          # of what is appeneded to the url first so this can change bittrexbalances.url to something different that bittrexURL
          # Also when Bittrex says append apikey and nonce to request they mean append it to the request including the params
          # this is what test is.
          nonceBit = time.time()
          bittrexURL = "https://bittrex.com/api/v1.1/account/getbalances?" + "nonce=" + str(nonceBit) + "&" + "apikey=" + BittrexKey
          #You got this right
          BittrexSign = hmac.new(BittrexSecret,bittrexURL,hashlib.sha512).hexdigest()
          bittrexHeader = {"apisign":BittrexSign}
          bittrexParams = {"apikey":BittrexKey, "nonce":nonceBit}
          bittrexbalances = requests.get("https://bittrex.com/api/v1.1/account/getbalances",params=bittrexParams,headers=bittrexHeader).json()
          
          
          #Poloniex
          nonce = time.time()
          poloParams = {"command" : "returnBalances", "nonce" : nonce}
          post = urllib.urlencode(poloParams)
          sig = hmac.new(poloniexSecret, post, hashlib.sha512).hexdigest()
          head = {"Key" : poloniexKey, "Sign" : sig}
          PoloniexBalances = requests.post(poloniexURL, data=poloParams, headers=head).json()

          allArr = bittrexbalances['result']
          dig = 0
          for index, o in enumerate(allArr):
              if o['Currency'] == "DASH":
                dig = index
        
          balances["Cryptsy"] = [float(cryptsybalances['return']['balances_available']['BTC']) , float(cryptsybalances['return']['balances_available']['DASH'])]
          balances["Bittrex"] = [bittrexbalances['result'][0]['Available'], bittrexbalances['result'][dig]['Available']]
          balances["Poloniex"] = [float(PoloniexBalances['BTC']), float(PoloniexBalances['DASH'])]
     
          print balances
          print "Total BTC: " + str(balances['Cryptsy'][0] + balances['Bittrex'][0] + balances['Poloniex'][0])
          print "Total DASH: " + str(balances['Cryptsy'][1] + balances['Bittrex'][1] + balances['Poloniex'][1])
          return balances

        except:
          print "Something went wrong when I was checking the balances. Let me try again in 30 seconds"
          time.sleep(30)
          return getBalances()


def needBTCRestock():
    global waitWhile
    balan = getBalances()
    for market,balance in balan.iteritems():
        if balance[0] < waitWhile:
            return True
    return False

def needDASHRestock():
    global waitWhile
    global const
    
    balan = getBalances()
    for market,balance in balan.iteritems():
        if balance[1] < mainDash/2 or (const == 1 and balance[1] < eqDRK):
            return True
    return False

def getLargestBtcMarket():
    global balances
    global waitWhile
    tmp = []
    for market,balance in balances.iteritems():
        tmp.append(balance[0])
    
    maxAmt = max(tmp)
    minAmt = min(tmp)

    bigMark = ""
    lilMark = ""

    for market,balance in balances.iteritems():
        if balance[0] == maxAmt:
            bigMark = market
        elif balance[0] == minAmt:
            lilMark = market
    return [bigMark,maxAmt,lilMark,minAmt]


def getLargestDashMarket():
    global balances

    tmp = []
    for market,balance in balances.iteritems():
        tmp.append(balance[1])

    maxAmt = max(tmp)
    minAmt = min(tmp)

    bigMark = ""
    lilMark = ""
    
    for market,balance in balances.iteritems():
        if balance[1] == maxAmt:
            bigMark = market
        elif balance[1] == minAmt:
            lilMark = market
    return [bigMark,maxAmt,lilMark,minAmt]


def isInEquilibrum():
    global balances
    global waitWhile
    global eqDRK
    global checkTime
    
    r = []

    for market,amounts in balances.iteritems():
        if amounts[0] < waitWhile or amounts[1] < eqDRK:
            return False
    return True

def reseteqDRK():
    global eqDRK
    global mainDash
    global checkTime
    
    info = getLargestDashMarket()
    
    while int(info[3]) < mainDash/2:
        print "Can't change eqDrk at the moment. Let my try to refill then Im going to sleep for 90 seconds"
        
        print needToRefillDash
        print needToRefillBtc
        
        if theNeed():
            refillTheNeed()
        
        time.sleep(90)
        getBalances()
        info = getLargestDashMarket()
    
    eqDRK = int(info[3])
    
    if eqDRK < mainDash:
        checkTime = time.time()



def BTCWait(market):
    global balances
    global waitWhile

    while balances[market][0] < waitWhile:
        print "Waiting for BTC to refill. Im going to sleep for 90 seconds!"
        time.sleep(90)
        getBalances()


def equilibrium(amountToBuy=0, buyfrommarket="", selltomarket="", sale=False, buyorsell="None"):
    
    global needToRefillDash
    global needToRefillBtc
    global eqBTC
    global balances
    global eqDRK
    global checkTime
    
    getBalances()
    

    if sale == True:
        if buyfrommarket == 'Poloniex':
            amountToBuy = round((amountToBuy - (amountToBuy * 0.002)),8)
        
        if not(restockDASH(buyfrommarket,amountToBuy,selltomarket)):
            needToRefillDash[selltomarket] = needToRefillDash[selltomarket] + amountToBuy
            checkTime = time.time()

    if needBTCRestock():
        info = getLargestBtcMarket()
        if not(restockBTC(info[0],eqBTC - info[3],info[2])):
            needToRefillBtc[info[2]] = needToRefillBtc[info[2]] + (eqBTC - info[3])
            checkTime = time.time()
        else:
            BTCWait(info[2])

    if sale == False:
        if amountToBuy != 0:
            
            if buyfrommarket == 'Poloniex':
                amountToBuy = round((amountToBuy - (amountToBuy * 0.002)),8)

            needToRefillDash[selltomarket] = needToRefillDash[selltomarket] + amountToBuy
            checkTime = time.time()
        else:
            info = getLargestDashMarket()
            if int(info[1] - mainDash) > 0 and not(restockDASH(info[0],int(info[1] - mainDash),info[2])):
                needToRefillDash[info[2]] = needToRefillDash[info[2]] + amountToBuy
                checkTime = time.time()

    reseteqDRK()
    getBalances()

def theNeed():
    global needToRefillBtc
    global needToRefillDash

    for i,j in needToRefillDash.iteritems():
        if j != 0:
            return True

    for i,j in needToRefillDash.iteritems():
        if j != 0:
            return True

    return False


def refillTheNeed():
    global needToRefillBtc
    global needToRefillDash
    global eqDRK
    

    info = getLargestDashMarket()
    info2 = getLargestBtcMarket()

    for market,amount in needToRefillDash.iteritems():
        if (info[1] - mainDash) >= amount and needToRefillDash[market] != 0:
            if restockDASH(info[0],amount,market):
                print "Ok Successfully restocked the need! -- DASH"
                needToRefillDash[market] = 0

    for market,amount in needToRefillBtc.iteritems():
        if (info2[1] - eqBTC) >= amount and needToRefillBtc[market] != 0:
            if restockBTC(info2[0],amount,market):
                print "Ok Successfully restocked the need! -- BTC"
                needToRefillBtc[market] = 0




def buyConfirmed(oldbalancesDASHNUM, marketname, amountToBuy):
    newbalances = getBalances()
    startTime = time.time()
    
    if marketname == 'Poloniex':
        amountToBuy = round((amountToBuy - (amountToBuy * 0.002)),8)

    ii = round(oldbalancesDASHNUM + amountToBuy,8)
    
    #The reason for round is there is a really weird case where 3.2456754 + 3 returns 6.2939491400000005 but Bittrex balance is 6.29394914. So even though the buy of 3 DASH was successful (prevDASHAMT was 3.2456754), the loop is not broken. (6.29394914 < 6.2939491400000005 evalutes True). So now it is rounded to 8 decimal places.--Even werider is now it returns the right value........(Keep round tho)
    while newbalances[marketname][1] < ii:
        print "oldbalancesDASHNUM " + str(oldbalancesDASHNUM)
        print "marketName " + marketname
        print amountToBuy
        print "Seems like the buy order in " + marketname + " has not been completed yet. I'll wait =)"
        
        if (time.time() >= (startTime + 1800)):
            return False
            break
        
        newbalances = getBalances()

    return True

def sellConfirmed(oldbalancesBTCNUM, marketname, amountToBuy, highBuy):
    newbalances = getBalances()
    startTime = time.time()
    
    if marketname == "Cryptsy":
        tip = 0.0024
    elif marketname == 'Bittrex':
        tip = 0.0025
    elif marketname == 'Poloniex':
        tip = 0.002
    
    
    iSold = round( ((amountToBuy * highBuy) - ((amountToBuy * highBuy) * tip)) , 8)
    
#Excahnges round some times so a sell may be fullfilled but the math may be off by 0.00000001 so I will subtract this ammount

    while newbalances[marketname][0] < round((round(oldbalancesBTCNUM + iSold,8) - 0.00000001)):
    
        print "Seems like the sell order in " + marketname + " has not been completed yet. I'll wait =)"
        
        if (time.time() >= (startTime + 1800)):
            return False
            break
        
        newbalances = getBalances()


    return True

def Cryptsy_Bittrex_Poloniex_Fee_Ok(sell,buy, amt, lowSell, highBuy, newbalances):
    
    if sell == 'Cryptsy' or buy == 'Cryptsy':
        tip = 0.0024
    elif sell == 'Bittrex' or buy == 'Bittrex':
        tip = 0.0025
    elif sell == 'Poloniex' or buy == 'Poloniex':
        tip = 0.002
    
    if (((amt * highBuy) - ((amt * highBuy) * tip)) < (amt * lowSell)):
        if sell == 'Cryptsy':
            print "Sorry looks like the Cryptsy fee stops me from profiting. I can't proceed! -- Cryspty sell"
        elif sell == 'Bittrex':
            print "Sorry looks like the Bittrex fee stops me from profiting. I can't proceed! -- Bittrex sell"
        elif sell == 'Poloniex':
            print "Sorry looks like the Poloniex fee stops me from profiting. I can't proceed! -- Bittrex sell"
        
        return False
    
    if (((amt * lowSell) + ((amt * lowSell) * tip)) > (amt * highBuy)):
        if buy == 'Cryptsy':
            print "Sorry looks like the Cryptsy fee stops me from profiting. I can't proceed! -- Cryptsy buy"
        elif buy == 'Bittrex':
            print "Sorry looks like the Bittrex fee stops me from profiting. I can't proceed! -- Bittrex buy"
        elif buy == 'Poloniex':
            print "Sorry looks like the Poloniex fee stops me from profiting. I can't proceed! -- Bittrex buy"
        
        return False


    return True



def tmpProfit(lowSell, highBuy, amtBuy, buy, sell):

    if  buy == 'Cryptsy':
        tip = 0.0024
    elif buy == 'Bittrex':
        tip = 0.0025
    elif buy == 'Poloniex':
        tip = 0.002


    buyPrice = ((amtBuy * lowSell) + ((amtBuy * lowSell) * tip))

    print "Buy Price is: " + str(buyPrice)

    if sell == 'Cryptsy':
        tip = 0.0024
    elif sell == 'Bittrex':
        tip = 0.0025
    elif sell == 'Poloniex':
        tip = 0.002

    sellPrice = ((amtBuy * highBuy) - ((amtBuy * highBuy) * tip))


    print "Sell Price is: " + str(sellPrice)

    return (sellPrice - buyPrice)



#const = 1 only in the first loop. After that it is changed to 2 to signify the first loop is over
while const == 1 or const == 2:
    print "My total profit so far is: " + str(profit)
    print "Need to refill: " + str(needToRefillDash)
    print checkTime
    allbuy = {}
    allsell = {}
    #Variable the when set to True will not enter the 'if' statement that issues buys and sells
    emergstop = False
    print "Looking..."

#Get balances - BTC balance is the first number and XPY balance is the second


    if checkbalance == True or const == 1:
        balances = getBalances()


#Checks to see if Minny should sleep till restocked
    if not(isInEquilibrum()):
        equilibrium()


    if checkTime != None and (time.time() >= checkTime + 120):
        print "Checking eqDRK"
        balances = getBalances()
        reseteqDRK()
        
        if theNeed():
            refillTheNeed()
        
        if eqDRK >= mainDash:
            checkTime = None
        else:
            checkTime = time.time()


    print "eqDRK is: " + str(eqDRK)


#Gets cryptsy buy price
    print "Getting Cryptsy Buy and Sell prices..."
    try:
        tmp = requests.get("http://pubapi1.cryptsy.com/api.php?method=singleorderdata&marketid=155",timeout=10).json()
        
        if tmp['success'] != 1:
            print "Error getting Cryptsy buy price.... Restarting loop"
            continue

        cryptbuy = float(tmp['return']['DASH']['buyorders'][0]['price'])
        cryptbuyamount = float(tmp['return']['DASH']['buyorders'][0]['quantity'])

        cryptsell = float(tmp['return']['DASH']['sellorders'][0]['price'])
        cryptsellamount = float(tmp['return']['DASH']['sellorders'][0]['quantity'])

    except:
        print "Error getting Cryptsy buy price.... Restarting loop"
        continue


    allbuy[cryptbuy] = "Cryptsy"
    allsell[cryptsell] = 'Cryptsy'



#Gets Poloniex Buy and Sell prices

    print "Getting Poloniex Buy and Sell prices"
    try:
        polo = requests.post("http://poloniex.com/public?command=returnOrderBook&currencyPair=BTC_DASH&depth=5",timeout=10).json()
        polobuy = float(polo['bids'][0][0])
        polobuyamount = polo['bids'][0][1]

        polosell = float(polo['asks'][0][0])
        polosellamount = polo['asks'][0][1]

    except:
        print "Error getting Poloniex prices.... Restarting loop"
        continue

    allbuy[polobuy] = 'Poloniex'
    allsell[polosell] = 'Poloniex'


#Bittrex gives option to get both buy and sell prices in one api call
    print "Getting Bittrex Buy and Sell prices..."
    try:
        tmpHeader = {"Content-Type": "application/json"}
        tmpParam = {"market" : "BTC-DASH", "type" : "both"}
        bittrexReq = requests.get("https://bittrex.com/api/v1.1/public/getorderbook", params=tmpParam,headers=tmpHeader,timeout=10)
        bittrex = bittrexReq.json()
        if (bittrex['success'] == True):
            bittrexbuy = bittrex['result']['buy'][0]['Rate']
            bittrexbuyamount = bittrex['result']['buy'][0]['Quantity']
            bittrexsell = bittrex['result']['sell'][0]['Rate']
            bittrexsellamount = bittrex['result']['sell'][0]['Quantity']
        else:
            print "Error getting Bittrex prices.... Restarting loop"
            continue
    except:
            print "Error getting Bittrex prices.... Restarting loop"
            continue

    allbuy[bittrexbuy] = 'Bittrex'
    allsell[bittrexsell] = 'Bittrex'

#Sorts the buy and sell markets for highest buy price and lowest sell price

    temp = allbuy.keys()
    temp.sort(reverse=True)

    temp2 = allsell.keys()
    temp2.sort()


#    print allbuy
#    print allsell

#    print temp
#    print temp2
#highestbuy is the highest buy price and lowestsell is the lowest sell price
    highestbuy = temp[0]
    lowestsell = temp2[0]



#Selltomarket is the market that Minny will sell XPY in and buyfrommarket is the market Minny will purchase XPY from
    selltomarket = allbuy[highestbuy]
    buyfrommarket = allsell[lowestsell]


#totalcanbuy is the the most XPY the buy market can buy
    totalcanbuy = (balances[buyfrommarket][0] - .0001)/lowestsell


# This check is actually not needed since Minny never detects the outlier price. -- Is needed for Cryptsy
# This check prevents outliers. If someone dumps a coin at an extrememly low price or someone buys a coin above market value..
# the exchange will already fullfill the order by giving it the highest buyer or lowest seller (depending on if the outlier was a sell or buy
# Here is an example: if the price is around 0.0025 BTC for 1 XPY, and someone sells 1 XPY at 0.001 BTC/XPY then Minny will pick the lowestSell as
# 0.001. But since this price is less than the current buy price (assume its 0.002) -- the market will fulfill this order at the current buy price. So the seller will recieve 0.002 BTC instead of 0.001. The problem is Minny will issue a buy order for 0.001 but this will not get fulfilled
# Vice Versa, if the sell price is (0.002) and someone issues a buy for 1 XPY at (0.003) then the market will fulfill that order with the (0.002) sell which means the buyer will recieve more XPY than he posted (the amount is calculated by (the total BTC the buyer was willing to spend)/(the current sell price). But again, Minny will issue a sell that is for 0.003 when this will just get pushed down the list. Only buf with this is if a dump and an high buy are issued at the same time. -- But this is so rare it probably wouldnt happen.

    if cryptbuy > cryptsell or bittrexbuy > bittrexsell:
        emergstop = True
        print "The buy price was greater than the sell price -- The market will autmotically fullfill the order"


#canisell is the most the buy order will accept. NOT HOW MUCH I CAN SELL FROM MY WALLET.
# Example -- I can have 30 XPY to sell but the buy order only is buying 10. In this case canisell
# will equal 10.

    if selltomarket == 'Cryptsy':
        canisell = cryptbuyamount
    elif selltomarket == 'Bittrex':
        canisell = bittrexbuyamount
    elif selltomarket == 'Poloniex':
        canisell = polobuyamount





#Gets the amount to buy based only on the buy order.
    print "Getting amountToBuy"
    if buyfrommarket == 'Cryptsy':
        amountToBuy = amount(num=cryptsellamount, totalbuy=totalcanbuy)
    elif buyfrommarket == 'Bittrex':
        amountToBuy = amount(num=bittrexsellamount, totalbuy=totalcanbuy)
    elif buyfrommarket == 'Poloniex':
        amountToBuy = amount(num=polosellamount, totalbuy=totalcanbuy)

#Readjusts amountToBuy based on canisell. This makes sure that Minny only buys an amount that she can sell
#### AGAIN canisell IS NOT HOW MUCH MINNY CAN SELL FROM THE WALLET. IT IS HOW MUCH THE BUY ORDER IS BUYING ####
    if amountToBuy <= canisell:
        print "=) amountToBuy is less than canisell."
        amountToSell = amountToBuy
    elif canisell <= eqDRK:
        print "=) amountToBuy is NOT less than canisell but I changed it"
        amountToBuy = canisell
        amountToSell = amountToBuy
    else:
        print "amountToBuy is wrong! Emergency Stop!"
        emergstop = True



#Checkbalance is set to False to stop Minny from checking the balances when no buy or sell was made.
#It is later set to true when a buy or sell was made
    checkbalance = False

#const is set to 2 to show that the first loop run has ended
    const = 2
    print "Amount to buy: " + str(amountToBuy) + " at " + str(lowestsell) + " in " + buyfrommarket
    print "Amount to sell: " + str(amountToSell) + " at " + str(highestbuy) + " in " + selltomarket
    print "Checking if I can make a profit =)"

#This checks if Minny can sell amountToBuy FROM THE WALLET.
# Example- if amountToBuy is 5 when it is first set, but the amount Minny can sell is only 4 (because the buy order is only buying 4)
# amountToBuy is then changed to 4. But if there are only 3 XPY in the selltomarket wallet, amountToBuy needs to be adjusted to 3
# so Minny can sell that amount in the selltomarket
    if balances[selltomarket][1] < amountToBuy and balances[selltomarket][1] <= canisell:
       print "Changed amountToBuy because the sell balance in sellmarket is less"
       amountToBuy = balances[selltomarket][1]
       amountToSell = amountToBuy


#This is where the magic happens =)
# This -- amountToBuy >= (eqXPY - 2) -- is a temparary line. Just testing to see if it will maximize
# profits by avoiding the sells that only bring in like 0.000048 profits
    temperProfit = tmpProfit(lowestsell, highestbuy, amountToBuy, buyfrommarket, selltomarket)
    print 'Profit would be ' + str(temperProfit)

    if emergstop == False and lowestsell < highestbuy and buyfrommarket != selltomarket and balances[buyfrommarket][0] >= (amountToBuy * lowestsell) and balances[selltomarket][1] >= amountToBuy and Cryptsy_Bittrex_Poloniex_Fee_Ok(selltomarket, buyfrommarket, amountToBuy, lowestsell, highestbuy, balances) and temperProfit >= 0.0001:
          print "Yes! I can make a profit!"
          print buyfrommarket
          print amountToBuy
          print lowestsell
        
          print "Sell in this market: " + str(selltomarket)
          print amountToSell
          print highestbuy
          print "canisell: " + str(canisell)
          #Trade is going to occur so checkbalance is set to True for next loop
          checkbalance = True
          
          #Buys, sells and restocks
          
          #With two bots running at the same time please note: If bot 1 refills btc in one market, prevBTCAMT can be the amount before refill. But balances will not be updated (since balances is update once when the program starts) so prevBTCAMT will be amount before deposit of 1st bot. But once the 1st deposit gets funded, prevBTCAMT does not change so when sell confirmed is called, it is automatically confirmed even though the trade may not have fullfilled.
          prevDASHAMT = balances[buyfrommarket][1]
          prevBTCAMT = balances[selltomarket][0]
          if buy(buyfrommarket, amountToBuy, lowestsell):
              if sell(selltomarket, amountToSell, highestbuy, buyfrommarket, lowestsell):
                  print "prev dASH AMT: " + str(prevDASHAMT)
                  if buyConfirmed(prevDASHAMT, buyfrommarket, amountToBuy) and sellConfirmed(prevBTCAMT, selltomarket, amountToBuy, highestbuy):
                    equilibrium(amountToBuy, buyfrommarket, selltomarket, sale=True, buyorsell=True)
                  else:
                    print "The buy or sell order hasn't completed for 30 minutes"
                    equilibrium(amountToBuy, buyfrommarket, selltomarket, sale=False, buyorsell=False)

                  profit = profit + temperProfit
                  print "My temp profit is: " + str(temperProfit)
                  print "My total profit so far is: " + str(profit)
                  print "Done =)"


