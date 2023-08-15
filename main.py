# Version 1 of SD Project
# Sude Fidan 21068639, William Barnes 21031340, Fiorella Scarpino 21010043, Jack Douet 21025153, Troy Akbulut 21015976

# Imports (pip install flask), (pip install flask-mysql), (pip install pymsql)

# Used to run the web app
from flask import Flask, render_template, request, redirect, session, url_for

# Interacting with the database
import pymysql
from flaskext.mysql import MySQL

# Other
from footballHelper import Player, findAverage
import json
from werkzeug.security import generate_password_hash, check_password_hash

# Flask boilerplate
app = Flask(__name__)

# Initialise session key
app.secret_key = "bf7g4fxw8fngsyivnfgsdnxfghkdsajvg fw4yf82ong82q3gmz82omgfxie gfvewyog f4o gf43bgnf28o4g2o8qxgf2qc"

# Configuration settings for accessing DB
mysql = MySQL()
app.config['MYSQL_DATABASE_USER'] = 'sdWork'
app.config['MYSQL_DATABASE_PASSWORD'] = 'HT8wxqxhjLSVLm3@'
app.config['MYSQL_DATABASE_DB'] = 'SD'
app.config['MYSQL_DATABASE_HOST'] = '167.235.155.84'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql.init_app(app)


# Home page
@app.route('/', methods=['GET', 'POST'])
def index():
    try:
        loggedIn = session['loggedin']
        isAdmin=session['isAdmin']
    except:
        loggedIn = False
        isAdmin = False

    # Cursor
    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # Initialise session variables if not already available
    if not session.get('playerData'):
        session['playerData'] = None
        session['allPlayerData'] = None

    # Get all data now to reduce future calls to the database
    cursor.execute("SELECT * FROM Players;")
    allPlayers = cursor.fetchall()
    cursor.execute("SELECT * FROM Teams;")
    allTeamData = cursor.fetchall()

    cursor.close()
    conn.close()

    # Starting from player 0 in the table
    x = 0 

    #For each row in all Players Dict
    for row in allPlayers:

        # We check each player against every team
        for items in allTeamData:

            # If a players current Team matches a team in the teams dict
            if allPlayers[x]['currentTeam'] == items['TeamName']:

                # We append there location and there manager onto the end of allPlayers
                allPlayers[x]['teamLocation'] = items['Location']
                allPlayers[x]['teamManager'] = items['Manager']

        # Update Date variables with correct formatting to strip out date time
        birthDate = allPlayers[x]['DateOfBirth'].strftime('%d/%m/%Y')
        allPlayers[x]['DateOfBirth'] = birthDate
        date_signed = allPlayers[x]['dateSigned'].strftime('%d/%m/%Y')
        allPlayers[x]['dateSigned'] = date_signed
        contract_signed = allPlayers[x]['startContract'].strftime('%d/%m/%Y')
        allPlayers[x]['startContract'] = contract_signed

        # Going through each player
        x = x + 1

    # Setting all session data to the new allPlayers Dict    
    session['allPlayerData'] = allPlayers
    session['allTeamData'] = allTeamData

    # Take all players from session data to put into the two players drop downs on comparison page.
    players = []

    for player in session['allPlayerData']:
        players.append(Player(player))

    # form action
    if request.method == 'POST' and 'playerName' in request.form:
        requestedUser = request.form['playerName']
        request_player(requestedUser)
        return redirect('/playerSearch')

    # Base render
    return render_template('homepage.html', players=players, loggedIn=loggedIn, isAdmin=isAdmin)

def request_player(playerName):

    # Will throw an error if there is no connection
    try:

        # Find the player in the database
            for row in session['allPlayerData']:
                if row['PlayerName'] == playerName:
                    playerData = row
                else:
                    pass
    except:
        msg = "No SQL Connection"
        return render_template('homepage.html', msg=msg)

    # Return an error message if no player was found
    if not playerData:
        msg = ("No Player found")
        return render_template('homepage.html', msg=msg)

    # Results from database is a string so we have to convert
    playerData['gamesWon'] = int(playerData['gamesWon'])
    playerData['gamesLost'] = int(
        (playerData['gamesPlayed'])) - playerData['gamesWon']
    playerData['gamesPlayed'] = int((playerData['gamesPlayed']))

    # Store the data in a session variable to use on the next page
    session['playerData'] = playerData
    return playerData

# All players page
@app.route('/players', methods=['GET', 'POST'])
def players():
    try:
        loggedIn = session['loggedin']
        isAdmin = session['isAdmin']
    except:
        loggedIn = False
        isAdmin = False
    
    
     # all players list
    players = []

    # Get all players from the session
    for player in session['allPlayerData']:
        players.append(Player(player))

    # redirecting to specific player
    if request.method == 'POST' and 'playerName' in request.form:
        # Get the name from user's input
        playerName = request.form['playerName']
        # request the player
        session['playerData'] = request_player(playerName)
        # Redirect user to the next page
        return redirect('/playerSearch')

    return render_template('players.html', allPlayers=players,loggedIn=loggedIn, isAdmin=isAdmin)

# Individual player page
@app.route('/playerSearch')
def playerSearch():
    try:
        loggedIn = session['loggedin']
        isAdmin = session['isAdmin']
    except:
        loggedIn = False
        isAdmin = False  
    # Get all data of the player from the session (set on home page)
    player = Player(session['playerData'])

    # Tally the results of the players 5 most recent games
    playerGame_results = player.tallyResults()

    # Find the average performance across all players
    game_averages = findAverage(session['allPlayerData'])

    # Find the transfer value predictions for the next 5 games
    playerPrediction = player.predict()

    # Data for graphing results on a pie chart
    sizes = [player.getWins(), player.getLosses()]
    labels = ('Matches Won', 'Matches Lost')

    # Data for graphing results on a line graph
    x_labels = ['FG1', 'FG2', 'FG3', 'FG4', 'FG5']

    return render_template('playerSearch.html', player=player,
                           playerPrediction=playerPrediction, transferValue=f"{player.getValue():.0f}k",
                           sizes=json.dumps(sizes), data1=json.dumps(playerGame_results),
                           data2=json.dumps(game_averages), labels=json.dumps(labels), xlabels=json.dumps(x_labels),loggedIn=loggedIn, isAdmin=isAdmin)


@app.route('/playerCompare', methods=('GET', 'POST'))
def playerCompare():
    try:
        loggedIn = session['loggedin']
        isAdmin=session['isAdmin']
    except:
        loggedIn = False
        isAdmin = False  

    # Empty array for all players
    players = []

    # Take all players from session data to put into the two players drop downs on comparison page.
    for player in session['allPlayerData']:
        players.append(Player(player))

    return render_template('playerCompare.html', players=players,loggedIn=loggedIn, isAdmin=isAdmin)

@app.route('/playerComparison', methods=('GET', 'POST'))
def playerComparison():
    try:
        loggedIn = session['loggedin']
        isAdmin=session['isAdmin']
    except:
        loggedIn = False
        isAdmin = False
    # Checks if both players have been selected
    if request.method == 'POST' and 'playerOne' in request.form and 'playerTwo' in request.form:
        
        # Uses request_player function to get all DB data for selected players.
        playerOneInput = request_player(request.form['playerOne'])
        playerTwoInput = request_player(request.form['playerTwo'])

        # Create player objects from DB data.
        playerOne = Player(player=playerOneInput)
        playerTwo = Player(player=playerTwoInput)

        # Tally the results of the players' 5 most recent games
        playerOneGame_results = playerOne.tallyResults()
        playerTwoGame_results = playerTwo.tallyResults()

        # Find the average performance across all players
        game_averages = findAverage(session['allPlayerData'])

        # Find the transfer value predictions for the next 5 games
        playerOnePrediction = playerOne.predict()
        playerTwoPrediction = playerTwo.predict()

        # Data for graphing results on a pie chart
        sizesOne = [playerOne.getWins(), playerOne.getLosses()]
        sizesTwo = [playerTwo.getWins(), playerTwo.getLosses()]
        labels = ('Matches Won', 'Matches Lost')

        # Data for graphing results on a line graph
        x_labels = ['FG1', 'FG2', 'FG3', 'FG4', 'FG5']

        return render_template('playerComparison.html', playerOne=playerOne, playerTwo=playerTwo,
                           playerOnePrediction=playerOnePrediction, playerTwoPrediction=playerTwoPrediction,
                           transferValueOne=f"{playerOne.getValue():.0f}k", transferValueTwo=f"{playerTwo.getValue():.0f}k",
                           sizesOne=json.dumps(sizesOne), sizesTwo=json.dumps(sizesTwo), dataOne1=json.dumps(playerOneGame_results),
                           dataTwo1=json.dumps(playerTwoGame_results),data2=json.dumps(game_averages), 
                           labels=json.dumps(labels), xlabels=json.dumps(x_labels), zip=zip, loggedIn=loggedIn, isAdmin=isAdmin)


@app.route('/login', methods=['GET', 'POST']) # Login Page
def login():
    try:
        loggedIn = session['loggedin']
        isAdmin = session['isAdmin']
    except:
        loggedIn = False
        isAdmin = False
    #connection to database 
    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    #error message if all goes wrong 
    msg = ''

    if request.method == 'POST':
        # Creating variables for easy use later on
        password = request.form['password']
        username =  (request.form.get('username'))

        #Make sure the account actually exists in the database 
        print("Username", username)
        cursor.execute('SELECT * FROM Users WHERE Username = %s', (username))
        #Fetch the record and return the result of said record
        account = cursor.fetchone()
        cursor.close()
        conn.close()

        # if account does not exist, kick back to login screen
        if not account:
            msg = 'Incorrect username or password'
            return render_template('login.html', msg = msg)
        
        # Check password entered against hashed value
        result = False
        db_hashed = account['Password']
        result = check_password_hash(db_hashed, password)

        # if password wrong, kick back to login screen
        if not result:
            msg = "Incorrect password"
            return render_template('login.html', msg = msg)

        session['loggedin'] = True
        session['loggedInID'] = account['Username']
        session['Email'] = account['Email']

        # If privilege is equal to 1/True its going to set the session isAdmin to true
        if account['Privilege'] == 1: 
            session['isAdmin'] = True
        else:
            session['isAdmin'] = False
            
        return redirect(url_for('profile'))
    else:
        return render_template('login.html', msg = msg)


@app.route('/profile', methods=('GET', 'POST'))
def profile():
    try:
        loggedIn = session['loggedin']
        isAdmin = session['isAdmin']
    except:
        loggedIn = False
        isAdmin = False

    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    if loggedIn == True:
        players = []

        cursor.execute("SELECT * FROM Favorites WHERE User = %s", session['loggedInID'])
        totalFav = cursor.fetchall()
        conn.close()

        for row in totalFav:
            for player in session['allPlayerData']:
                if player['PlayerName'] == row['Player']:
                    players.append(Player(player))

        # redirecting to specific player
        if request.method == 'POST' and 'playerName' in request.form:

            # Get the name from user's input
            playerName = request.form['playerName']

            # request the player
            session['playerData'] = request_player(playerName)

            # Redirect user to the next page
            return redirect('/playerSearch')
        
        return render_template('loginSuccess.html', allPlayers=players,loggedIn=loggedIn, isAdmin=isAdmin)
    else:
        return redirect(url_for('login'))

@app.route('/logout')
def logout():

    # If the user logs out of their session it just sets all there session data to 'None'
    session.pop('loggedin', None)
    session.pop('loggedInID', None)
    session.pop('Email', None)
    session.pop('isAdmin', None)
    return redirect(url_for('login'))

@app.route('/register', methods=('GET', 'POST'))
def register():
    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    msg = ""

    #Check if the user is already logged in
    try:
        if session['loggedin'] == True:
            return redirect(url_for('profile'))
    except:
        loggedIn = False

    # Fetch values from form
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:

        # Set Variables based off values from the form
        email = request.form['email']
        password = request.form['password']
        usernames =  (request.form.get('username'))

        # Create password hash
        hashed_password = generate_password_hash(password)

        # Fetching all results from database with supplied email and username this is to make sure we dont already have an existing user
        totalUsers = cursor.execute("SELECT * FROM Users WHERE Username = %s", usernames)
        totalEmail = cursor.execute("SELECT * FROM Users WHERE Email = %s", email)
        if (totalUsers == 0):
            if (totalEmail == 0):
                cursor.execute("INSERT INTO `Users` (`Username`, `Password`, `Email`, `Privilege`) VALUES (%s, %s, %s, '%s');", (usernames, hashed_password, email, 0)) #auto increment 
                conn.commit()
                print("Committed")
                cursor.close()
                conn.close()
                msg = 'User Account Created'
                return render_template('login.html')
            else:
                msg = 'Email already exists'
                print("non")
        else:
            msg = 'Username already exists'
            print("non")
    return render_template('register.html', msg=msg, loggedIn=loggedIn)

@app.route('/addNewFavorite/<string:x>', methods=['POST'])
def addNewFavorite(x):
    # Grabs the users favorite and stores it 
    x = json.loads(x)
    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # Grabs all the users current Favorites
    cursor.execute("SELECT * FROM Favorites WHERE User = %s", session['loggedInID'])
    totalFav = cursor.fetchall()
    totalCount = 0
    for row in totalFav:
        if(row['Player']==x):
            totalCount =+1

    # If the new player selected does not equal any of the user's current favorites we commit it to the table
    if (totalCount ==0):
        cursor.execute("INSERT INTO `Favorites` (`FavID`, `User`, `Player`) VALUES ('%s', %s, %s);", (0, session['loggedInID'], x)) #auto increment 
        conn.commit()
        conn.close()
    else:
        print("User has already added this as a fave")
    return ('Info Received Successfully')

@app.route('/removeFave/<string:x>', methods=['POST'])
def removeFave(x):
    x = json.loads(x)
    conn = mysql.connect()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    print("Trying to remove", x)
    cursor.execute("DELETE FROM Favorites WHERE User = %s AND Player =%s", (session['loggedInID'], x))
    conn.commit()
    conn.close()



@app.route('/admin', methods=('GET','POST'))
def admin():
    try:
        loggedIn = session['loggedin']
        isAdmin = session['isAdmin']
    except:
        loggedIn = False
        isAdmin = False
    
    if isAdmin == True:
        # all players list
        players = []

        # Get all players from the session
        for player in session['allPlayerData']:
            players.append(Player(player))

        teamsList = []

        for teams in session['allTeamData']:
            teamsList.append(teams)

        if request.method == 'POST':
            player = request.form['playerName']
            operation = request.form['submit']

            conn = mysql.connect()
            cursor = conn.cursor(pymysql.cursors.DictCursor)

            cursor.execute("SELECT * FROM Players WHERE PlayerName = %s;", (player))
            foundPlayer = cursor.fetchall()
            foundPlayer = foundPlayer[0]

            cursor.execute("SELECT * FROM Teams WHERE TeamName = %s;", (foundPlayer['currentTeam']))
            foundTeam = cursor.fetchall()
            foundTeam = foundTeam[0]

            foundPlayer.update(foundTeam)

            tempDOB = foundPlayer['DateOfBirth']

            foundPlayer['teamLocation'] = foundPlayer['Location']
            foundPlayer['teamManager'] = foundPlayer['Manager']
            foundPlayer['DateOfBirth'] = foundPlayer['DateOfBirth'].strftime('%d/%m/%Y')
            foundPlayer['startContract'] = foundPlayer['startContract'].strftime('%d/%m/%Y')

            player = Player(foundPlayer)
            player.dateOfBirth = tempDOB

            cursor.close()
            conn.close()

            return render_template('adminFunction.html', player=player, operation=operation,loggedIn=loggedIn, isAdmin=isAdmin, teamNames=teamsList)
            

        return render_template('admin.html', loggedIn=loggedIn, isAdmin=isAdmin, players=players)
    else:
        print("User is not an admin")
    return render_template('homepage.html')


@app.route('/modifyPlayer', methods=('GET', 'POST'))
def modifyPlayer():

    if request.method == 'POST':
        newDOB = request.form['dob']
        newGender = request.form['gender']
        newClub = request.form['club']
        newDate = request.form['dateSigned']
        newSalary = request.form['salary']

        playerName = request.form['playerName']


        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        sqlStatement = "UPDATE Players SET DateOfBirth = %s, Gender = %s, currentTeam = %s, dateSigned = %s, salary = %s WHERE PlayerName = %s"

        cursor.execute(sqlStatement, (newDOB, newGender, newClub, newDate, newSalary, playerName))

        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('admin'))

@app.route('/deletePlayer', methods=('GET', 'POST'))
def deletePlayer():
    if request.method == 'POST':
        playerName = request.form['playerName']

        conn = mysql.connect()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        sqlStatement = "DELETE FROM Players WHERE PlayerName = %s;"

        cursor.execute(sqlStatement, (playerName))

        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('admin'))
    
@app.route('/copyright')
def copyright():
    try:
        loggedIn = session['loggedin']
        isAdmin = session['isAdmin']
    except:
        loggedIn = False
        isAdmin = False

    return render_template('copyright.html',  loggedIn=loggedIn, isAdmin=isAdmin)
    
if __name__ == '__main__':
    app.run(debug=True)
