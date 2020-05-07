import csv;
import logging
from datetime import datetime, timedelta, date
import argparse
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

parser=argparse.ArgumentParser()
parser.add_argument('--file','-f', help='full path of the csv file', type= str, default= "sp500-10-year-daily-chart.csv")
print(parser.format_help())
args = parser.parse_args()

logger = logging.getLogger('dow_analysis')
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

index_data = []
years_to_analyze = 20;
date = datetime.today() - timedelta(days=years_to_analyze * 365);

with open(args.file) as index_data_file:
    csv_reader = csv.reader(index_data_file, delimiter=',')
    next(csv_reader)
    base_date=None
    for row in csv_reader:
        if base_date is None:
            base_date = datetime.strptime(row[0], '%m/%d/%y')
        if (datetime.strptime(row[0], '%m/%d/%y') >= date) and datetime.strptime(row[0], '%m/%d/%y').weekday() == 4:
            day = (datetime.strptime(row[0], '%m/%d/%y') - base_date).days
            try:
                r = {"date":datetime.strptime(row[0], '%m/%d/%y'),"day": day, "price": float(row[1]), "pe": float(row[5])}
            except:
                continue
            index_data.append(r)

def isClosedMountain(a,c):
    for index in range(a,c):
        index_price = index_data[index]['price']
        if index_price < index_data[a]['price'] or index_price < index_data[c]['price']:
            return False
    return True

def isClosedValley(a,c):
    for index in range(a,c):
        index_price = index_data[index]['price']
        if index_price > index_data[a]['price'] or index_price > index_data[c]['price']:
            return False
    return True


def isMontainFound(a, c):
    if index_data[c]['day'] - index_data[a]['day'] < 25:
        logger.debug("\t\t days less than 25 : "+str(index_data[c]['day'] - index_data[a]['day']))
        return None
    if isClosedMountain(a,c) is False:
        logger.debug("\t\t mountain has valleys")
        return None
    a_price = index_data[a]['price']
    c_price = index_data[c]['price']
    if a_price >= c_price:
        day = intersction(index_data[c-1], index_data[c], a_price)
        duration = day - index_data[a]['day']
        mountain_base_price = a_price
    else:
        day = intersction(index_data[a], index_data[a+1], c_price)
        duration = index_data[c]['day'] - day
        mountain_base_price = c_price
    max_price = mountain_base_price
    mountain_index = 0
    for i in range(a+1,c):
        if index_data[i]['price']> max_price:
            max_price = index_data[i]['price']
            mountain_index = i
    logger.debug("\t\t duration : "+str(duration)+" and difference "+ str(((max_price-mountain_base_price)/max_price)*100)+"%")
    if duration >=31 and mountain_base_price <=  max_price * 0.96:
        logger.debug("\t\t\tmountain found between : ("+str(a)+", "+str(c)+") bottom_day :"+str(mountain_index)+", max_price : "+str(max_price)+", base_price :"+str(mountain_base_price)+", date: "+index_data[mountain_index]['date'].strftime("%m/%d/%Y"))
        return mountain_index
    return None

def isValleyFound(a, c):
    if index_data[c]['day'] - index_data[a]['day'] < 25:
        logger.debug("\t\t days less than 25 : "+str(index_data[c]['day'] - index_data[a]['day']))
        return None
    if isClosedValley(a,c) is False:
        logger.debug("\t\t valley has peaks")
        return None
    a_price = index_data[a]['price']
    c_price = index_data[c]['price']
    if a_price >= c_price:
        day = intersction(index_data[a], index_data[a + 1], c_price)
        duration = index_data[c]['day'] - day
        valley_top_price = c_price
    else:
        day = intersction(index_data[c - 1], index_data[c], a_price)
        duration = day - index_data[a]['day']
        valley_top_price = a_price
    min_price = valley_top_price
    valley_index = 0
    for i in range(a+1,c):
        if index_data[i]['price']< min_price:
            min_price = index_data[i]['price']
            valley_index = i
    logger.debug("\t\t duration : "+str(duration)+" and differnce "+ str(((valley_top_price-min_price)/valley_top_price)*100)+"%")
    if duration >=31 and valley_top_price >=  min_price * 1.04:
        logger.debug("\t\t\tvalley found between : ("+str(a)+", "+str(c)+") bottom_day :"+str(valley_index)+", min_price : "+str(min_price)+", max_price :"+str(valley_top_price)+", date: "+index_data[valley_index]['date'].strftime("%m/%d/%Y"))
        return valley_index
    return None

# y=mx +c ; m = (y2-y1)/(x2-x1); y is price and x is days
def intersction(a1, a2, y3):
    y2 = a2['price']
    y1 = a1['price']
    x2 = a2['day']
    x1 = a1['day']

    m = (y2 - y1) / (x2 - x1)
    c = y2 - m*(x2)

    x3 = (y3 - c) / m
    return x3


def searchForValley(left_index, right_index):
    for index in range(left_index, right_index):
        logger.debug("\t detreming whether there is valley between ("+str(index)+", "+str(right_index)+")")
        valley_bottom_index = isValleyFound(index,right_index)
        if valley_bottom_index is not None:
            return [valley_bottom_index, index]
    return None

def searchForMountain(left_index, right_index):
    for index in range(left_index, right_index):
        logger.debug("\t detreming whether there is mountain between ("+str(index)+", "+str(right_index)+")")
        mountain_top_index = isMontainFound(index,right_index)
        if mountain_top_index is not None:
            return [mountain_top_index, index]
    return None

def getMessage(point_details,right_boundary,trend,isValley = True):
    message = trend+" ->"
    if isValley:
        message = message + " Valley discovered "
    else:
        message = message + " Mountain discovered"
    message = message + " at " + str(point_details[0])
    message = message + " between ("+ str(point_details[1])+", "+str(right_boundary)+")"
    message = message + " on " + index_data[point_details[0]]['date'].strftime("%m/%d/%Y")
    if isValley:
        message = message +". Valley bottom price : " + str(index_data[point_details[0]]['price'])
    else:
        message = message + ". Mountain top price : " + str(index_data[point_details[0]]['price'])
    if recent_bottom is not None:
        message = message +". Recent bottom was on " +recent_bottom['date'].strftime("%m/%d/%Y")+" at price : " + str(recent_bottom['price'])
    if recent_top is not None:
        message = message +". Recent top was on " +recent_top['date'].strftime("%m/%d/%Y")+" at price : " + str(recent_top['price'])
    return message

left_index = 0
look_for_mountain = False
look_for_valley = True
recent_top = None
recent_bottom = None
trend = None
chart_data=[]

for this_index, current_pointer in enumerate(index_data, start=3):
    logger.debug("at index : "+str(this_index))
    if this_index >= len(index_data):
        continue
    if look_for_valley and recent_top is not None and index_data[this_index]['price'] > recent_top['price']:
        #look_for_mountain = True
        #look_for_valley = False
        logger.info("*** search for (^) mountain, price went above recent top : " + str(recent_top['price'])+", current price : "+str(index_data[this_index]['price']))
        trend = "UP"
        #continue
    if recent_bottom is None or look_for_valley:
        logger.debug("finding valley between (" + str(left_index) +", " + str(this_index) + ")")
        valley_bottom_details = searchForValley(left_index, this_index)
        if valley_bottom_details is not None:
            valley_bottom = valley_bottom_details[0]
            if recent_bottom is not None and index_data[valley_bottom]['price'] > recent_bottom['price']:
                trend = "UP"
            else:
                trend = "DOWN"
            look_for_mountain = True
            look_for_valley = False
            left_index = valley_bottom
            logger.info(getMessage(valley_bottom_details,this_index,trend,True))
            chart_data.append([index_data[valley_bottom]['date'], index_data[valley_bottom]['price']])
            recent_bottom = index_data[valley_bottom]
        else:
            continue

    if look_for_mountain and index_data[this_index]['price'] < recent_bottom['price']:
        look_for_mountain=False
        look_for_valley = True
        logger.info("*** search for (v) valley, price went below recent bottom : "+str(recent_bottom['price'])+", current price : "+str(index_data[this_index]['price']))
        trend = "DOWN"
        continue

    if look_for_mountain:
        logger.debug("finding mountain between (" + str(left_index) + ", " + str(this_index) + ")")
        mountain_peak_details = searchForMountain(left_index, this_index)
        if mountain_peak_details is not None:
            mountain_peak = mountain_peak_details[0]
            if recent_top is not None and index_data[mountain_peak]['price'] > recent_top['price']:
                trend = "UP"
            else:
                trend = "DOWN"
            left_index = mountain_peak
            look_for_mountain = False
            look_for_valley = True
            logger.info(getMessage(mountain_peak_details, this_index, trend, False))
            chart_data.append([index_data[mountain_peak]['date'], index_data[mountain_peak]['price']])
            recent_top = index_data[mountain_peak]
        else:
            continue

print("recent_top : "+ str(recent_top))
print("recent_bottom : "+ str(recent_bottom))

chart_x = [e[0] for e in chart_data]
chart_y = [e[1] for e in chart_data]

plt.plot(chart_x,chart_y)
# beautify the x-labels
formatter = mdates.DateFormatter("%Y-%m-%d")
plt.gca().xaxis.set_major_formatter(formatter)

plt.show()




