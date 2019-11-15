 #This file is the server-side that create three tables in the database and handle requests from client
from flask import Flask, render_template, redirect, request
import sqlite3 as sql
import string
import random
import uuid
import datetime
app= Flask(__name__)
#app.debug=True
conn = sql.connect('database.db')
print "Opened database successfully";
#create 3 tables: table 1-to save long and short URL tables 2&3: to log redirections and errors
conn.execute('CREATE TABLE IF NOT EXISTS url (longURL TEXT PRIMARY KEY, newURL TEXT NOT NULL,joiningDate timestamp)')
conn.execute('CREATE TABLE IF NOT EXISTS redirectionslog (type TEXT,redirectDate timestamp)')
conn.execute('CREATE TABLE IF NOT EXISTS errorslog (type TEXT,errorDate timestamp)')
print "Tables created successfully";
conn.close()

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))
#----------------------------------------------------------------------------------------------------
#Render home page that contains input long URL
@app.route('/')
def index():
        return render_template('home.html')
#----------------------------------------------------------------------------------------------------
#Gather statistics information from the database and render them into statistics file
@app.route('/stats')
def stat():
    #Initilize statistics variables to zero
    rowsnum=lastminutenum=lasthournum=lastdaynum=lmr=lhr=ldr=lme=lhe=lde=0
    msg=""
    try:
         con = sql.connect("database.db")
         con.row_factory = sql.Row
         #Get the number of URL's
         rowresult = con.cursor()
         rowresult.execute('select COUNT(*) from url')
         rowsnum = rowresult.fetchone()[0];
         #Get the number of URL's that inserted in the last minute.
         minuteresult = con.cursor()
         da=(datetime.datetime.now() - datetime.timedelta(minutes = 1))
         minuteresult.execute("""select COUNT(*) from url where joiningDate >= ?""",[da])
         lastminutenum=minuteresult.fetchone()[0];
         #Get the number of URL's that inserted in the last hour.
         hourresult = con.cursor()
         da=(datetime.datetime.now() - datetime.timedelta(minutes = 60))
         hourresult.execute("""select COUNT(*) from url where joiningDate >= ?""",[da])
         lasthournum=hourresult.fetchone()[0];
         #Get the number of URL's that inserted in the last day.
         dayresult = con.cursor()
         da=(datetime.datetime.now() - datetime.timedelta(minutes = 1440))
         dayresult.execute("""select COUNT(*) from url where joiningDate >= ?""",[da])
         lastdaynum=dayresult.fetchone()[0];
         #Get the number of URL's redirections that happen in the last minute.
         minuteresult = con.cursor()
         da=(datetime.datetime.now() - datetime.timedelta(minutes = 1))
         minuteresult.execute("""select COUNT(*) from redirectionslog where redirectDate >= ?""",[da])
         lmr=minuteresult.fetchone()[0];
         #Get the number of URL's redirections that happen in the last hour.
         hourresult = con.cursor()
         da=(datetime.datetime.now() - datetime.timedelta(minutes = 60))
         hourresult.execute("""select COUNT(*) from redirectionslog where redirectDate >= ?""",[da])
         lhr=hourresult.fetchone()[0];
         #Get the number of URL's redirections that happen in the last day.
         dayresult = con.cursor()
         da=(datetime.datetime.now() - datetime.timedelta(minutes = 1440))
         dayresult.execute("""select COUNT(*) from redirectionslog where redirectDate >= ?""",[da])
         ldr=dayresult.fetchone()[0];
         #Get the number of errors that happen in the last minute.
         minuteresult = con.cursor()
         da=(datetime.datetime.now() - datetime.timedelta(minutes = 1))
         minuteresult.execute("""select COUNT(*) from errorslog where errorDate >= ?""",[da])
         lme=minuteresult.fetchone()[0];
         #Get the number of errors that happen in the last hour.
         hourresult = con.cursor()
         da=(datetime.datetime.now() - datetime.timedelta(minutes = 60))
         hourresult.execute("""select COUNT(*) from errorslog where errorDate >= ?""",[da])
         lhe=hourresult.fetchone()[0];
         #Get the number of errors that happen in the last day.
         dayresult = con.cursor()
         da=(datetime.datetime.now() - datetime.timedelta(minutes = 1440))
         dayresult.execute("""select COUNT(*) from errorslog where errorDate >= ?""",[da])
         lde=dayresult.fetchone()[0];

         msg=""

    except:
         con.rollback()
         log = con.cursor()
         log.execute("""INSERT INTO errorslog (type,errorDate)
         VALUES (?,?)""",("stats error",datetime.datetime.now()))
         con.commit()
         msg = "error in statistic operation"

    finally:
         return render_template('statistics.html',urlnum=rowsnum,lastminute=lastminutenum,msg=msg,
                                lasthour=lasthournum,lastday=lastdaynum,lastMinuteRedirections=lmr
                                ,lastHourRedirections=lhr,lastDayRedirections=ldr,lastMinuteerrors=lme,
                                lastHourerrors=lhe,lastDayerrors=lde
                                )
         con.close()
#----------------------------------------------------------------------------------------------------
#Get request==> input:short URL output:redirect to orginal URL
@app.route('/<name>')
def directTo(name):
   con = sql.connect("database.db")
   con.row_factory = sql.Row

   cur = con.cursor()
   cur.execute('select longURL from url where newURL = ?', [name])
   gotoorginal = cur.fetchone();
   #Check if URL exists and redirect to the original one (if URL does not exist render the notexist page).
   if gotoorginal:
       gotoorginalnew=gotoorginal[0]
       log = con.cursor()
       log.execute("""INSERT INTO redirectionslog (type,redirectDate)
       VALUES (?,?)""",(gotoorginalnew,datetime.datetime.now()))
       con.commit()
       con.close()
       if (gotoorginalnew.find("http",0,5)==-1):
           return  redirect("http://"+gotoorginalnew)
       else:
           return redirect(gotoorginalnew)
   else:
           return render_template('notexist.html')
#----------------------------------------------------------------------------------------------------
#Post request:input: long url output:if URL does not exist in DB generate new one else send back the one in the DB
@app.route('/addurl',methods=['POST'])
def addurl():
   if request.method == 'POST':
      try:
         inputurl = request.form['inputurl']

         with sql.connect("database.db") as con:
            curcheck = con.cursor()
            curcheck.execute('select newURL from url where longURL = ?', [inputurl])
            con.commit()
            exist = curcheck.fetchone()
            if exist:
                msg = "localhost:5000/"+exist[0]
            else:
                #generate new short URL that not used before
                while True:
                    existid=None
                    id=uuid.uuid4().hex[:6].upper()
                    idcheck= con.cursor()
                    idcheck.execute('select newURL from url where newURL = ?', [id])
                    con.commit()
                    existid = idcheck.fetchone()
                    if(existid==None):
                        break
                cur = con.cursor()
                cur.execute("""INSERT INTO url (longURL,newURL,joiningDate)
                VALUES (?,?,?)""",(inputurl,id,datetime.datetime.now()) )
                con.commit()
                msg ="localhost:5000/"+id

      except:
         con.rollback()
         log = con.cursor()
         log.execute("""INSERT INTO errorslog (type,errorDate)
         VALUES (?,?)""",("add url error",datetime.datetime.now()))
         con.commit()
         msg = "error in insert operation"

      finally:
         return render_template("result.html",msg = msg)
         con.close()
#----------------------------------------------------------------------------------------------------
#starting the server
if __name__ == '__main__':
    app.run()
