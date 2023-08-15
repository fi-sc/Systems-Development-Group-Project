# Imports
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

class Player:

    def __init__(self, player: dict) -> None:
        self.__player = player
        self.__name = player['PlayerName']
        self.__dateSigned = player['dateSigned']
        self.__club = player['currentTeam']
        self.__location = player['teamLocation']
        self.__manager = player['teamManager']
        self.__salary = player['salary']

        #age
        self.__dateOfBirth = player['DateOfBirth']
        self.__age = (date.today() - datetime.strptime(str(self.__dateOfBirth), '%d/%m/%Y').date()).days //365

        #gender identification
        if self.__player['Gender'] == 'M':
            self.__gender = 'Male'
        else:
            self.__gender = 'Female'

        #contract dates
        self.__startContract = player['startContract']
        self.__contractDuration = player['contractDuration']
        startContract = datetime.strptime(str(self.__startContract), '%d/%m/%Y').date()
        self.__endContract = startContract + relativedelta(years=int(self.__contractDuration))
        self.__weeksLeft = (self.__endContract - date.today()).days // 7

        #games
        self.__played = int(player['gamesPlayed'])
        self.__wins = int(player['gamesWon'])
        self.__losses = self.__played - self.__wins

        #game results
        self.__matches = []
        for key, result in player.items():
            if key.startswith('FG'):
                self.__matches.append(result)

        #win percentage
        self.__percentage = self.__wins / self.__played

        #transfer value
        self.__value = int(self.__salary) * self.__weeksLeft * self.__percentage

    def predict(self) -> dict[str, str]:
        # declare variables
        valueDict = {}
        moneyValue = self.__value

        # loop through next 5 matches
        for x in self.__matches:

            # value = current weekly salary x weeks left in the current contract x win percentage rate.
            # dividing by winrate so we can later multiply by the new winrate
            mutableVal = moneyValue / (self.__wins / self.__played)

            # adjust winrate accordingly 
            if x == 'W':
                self.__wins += 1
                self.__played += 1
            else:
                self.__losses += 1
                self.__played += 1

            # recalculate value
            mutableVal = mutableVal * (self.__wins / self.__played)

            # add the values to the dictionary
            valueDict[f"{mutableVal:.2f}"] = f"{(mutableVal - moneyValue):.2f}"

            # overwrite value for next cycle
            moneyValue = mutableVal

        # output the dictionary containing the values
        return valueDict
    def tallyResults(self):
        results = []
        for value in self.__matches:
            if value == 'W':
                results.append(1)
            else:
                results.append(0)
        return results

    # Creating Getters
    def getName(self):
        return self.__name
    def getDateSigned(self):
        return self.__dateSigned
    def getClub(self):
        return self.__club
    def getLocation(self):
        return self.__location
    def getManager(self):
        return self.__manager
    def getSalary(self):
        return self.__salary
    def getDateOfBirth(self):
        return self.__dateOfBirth
    def getStartContract(self):
        return self.__startContract
    def getContractDuration(self):
        return self.__contractDuration
    def getEndContract(self):
        return self.__endContract
    def getWeeksLeft(self):
        return self.__weeksLeft
    def getGender(self):
        return self.__gender
    def getPlayed(self):
        return self.__played
    def getWins(self):
        return self.__wins
    def getLosses(self):
        return self.__losses
    def getValue(self):
        return self.__value
    def getAge(self):
        return self.__age

def findAverage(playerData):
    game_results = []
    for player in playerData:
        player = Player(player)
        game_results.append(player.tallyResults())
    game_averages = []
    for i in range(5):
        total = 0
        count = 0
        for game in game_results:
            total += game[i]
            count += 1
        game_averages.append(total / count)
    return game_averages
