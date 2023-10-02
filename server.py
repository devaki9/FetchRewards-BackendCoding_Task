from collections import deque
from flask import Flask, request, jsonify
from datetime import datetime
"""
Creating a simple Python application using Flask framework to handle user transactions
to add, spend points and fetch the current points balance

Checks:
1. Ensure the points for payer are not negative
2. 

APIs:
1. /add
Accepts: payer, points and timestamp
Returns: Status code

2. /spend
Accepts: points
Returns: Status code, message(either succ/failure and reason)

3. /balance
Accepts: none
Returns: List of users with their remaining points
"""
app = Flask("rewards_app")

#variables
payers_list = {}
stat_cd=200
total_points=0
txns = deque()
headers = {
    'Content-type':'application/json', 
    'Accept':'application/json'
}

@app.route("/")
def home():
    return "Hello, Flask!"

"""
1. /add
Accepts: payer, points and timestamp
Returns: Status code
"""
#Always add points for one payer at a time
#Scope for adding points for multiple payers in the future
@app.route("/add", methods = ["POST"])
def add_points():
    request_data = request.get_json()
    print(request_data)
    payer = str(request_data['payer'])
    points = int(request_data['points'])
    datetime_str = str(request_data['timestamp'])
    timestamp = datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%SZ")
    #keep total points global
    global total_points #huh?
    global stat_cd
    global txns
    #When points are positive
    if points > 0:
        total_points += points
        txns.appendleft([payer, points, timestamp]) #Add to dequeue
        if payer in payers_list: #append to existing payers
            payers_list[payer] += points
        else:
            payers_list[payer] = points
    elif points < 0:   #when points are negative
        #case1 : when payer is present in list and post subtracting the points, result is negative
        if payer in payers_list and (payers_list[payer] + points ) < 0:
            stat_cd = 400
            return ("Incorrect value provided", int(stat_cd), headers)
        elif payer in payers_list and (payers_list[payer] - points ) > 0:
            payers_list[payer] += points
            total_points += points
            for numTxns in range(len(txns)-1, -1, -1):
                if txns[numTxns][0] == payer : # find the payer
                    difference = txns[numTxns][1] + points
                    if difference >= 0:
                        txns[numTxns][1] = difference
                        points = difference
                    else:
                        del txns[numTxns]
                        break
        else:
            stat_cd = 400
            return ("Incorrect values",int(stat_cd),headers)
    return("Fetch reward points added successfully", int(stat_cd),headers)

def sorting_key(lst):
    return lst[2]

@app.route("/spend", methods = ['DELETE'])
def delete_points():
    global total_points
    global stat_cd
    global txns
    request_data = request.get_json()
    
    #sorted this queue in oldest/earliest time format
    reduced_points = int(request_data['points'])

    if total_points < reduced_points:
        stat_cd=400
        return("Reward points are insufficient", int(stat_cd), headers)
    else:
        response_list = []
        sorted_txns = deque(sorted(txns, key=sorting_key))
        while( reduced_points > 0 and len(sorted_txns) >0):
            txn = sorted_txns.pop()
            reduced_points -= txn[1]
            diff = txn[1] - reduced_points
            if( reduced_points < 0):
                diff = txn[1] + reduced_points
                txn[1] = diff
                sorted_txns.append(txn)
            else:
                diff = txn[1]
            txn[1] = diff
            response_list.append(txn)
            payers_list[txn[0]]-= diff
            total_points-= diff

    for val in response_list:
        val[1] = -(val[1])
    return jsonify(response_list)

@app.route("/balance", methods = ["GET"])
def get_balance():
    return jsonify(payers_list)

if __name__ == "__main__":
    '''
    Starting the Flask application'''
    app.run(debug=True, host='localhost')