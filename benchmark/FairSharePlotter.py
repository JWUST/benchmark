import os
import shutil
import matplotlib as mpl
#mpl.use('Agg')
from pylab import *

import ast

class FairSharePlotter:

    def __init__(self, benchmarkGroupId, sessionIds, duration, window_length):
        self._groupId = benchmarkGroupId
        self._dirOutput = os.path.join(os.getcwd(), "plots", str(self._groupId))
        self._varyingParameter = None
        self._duration = duration
        self._window_length = window_length
        self._runs = self._collect_fair_share(sessionIds, self._duration, self._window_length)
        if not os.path.isdir(self._dirOutput):
            os.makedirs(self._dirOutput)


    def printFairShareStatistics(self, queries, sessionIds):
        intervals = int(round(self._duration / self._window_length))
        sessions = set(sessionIds)
        output = {}
        logStr = ""
        for runId, runData in self._runs.iteritems():
            output[runId] = ""
            for i in range(intervals):
                t = i * self._window_length
                output[runId] += str(t)
                for s in sessions:
                    output[runId] += " " + str(runData[runData.keys()[0]]['sessionStats'][s][i])
                output[runId] += "\n"
        for run in sorted(output.iterkeys()):
            logStr += "%s" % (output[run])    
        return logStr

    def _collect_fair_share(self, sessionIds, duration, window_length):
        runs = {}
        dirResults = os.path.join(os.getcwd(), "results", self._groupId)
        if not os.path.isdir(dirResults):
            raise Exception("Group result directory '%s' not found!" % dirResults)

        # --- Runs --- #
        for run in os.listdir(dirResults):

            dirRun = os.path.join(dirResults, run)
            if os.path.isdir(dirRun):
                runs[run] = {}

                # --- Builds --- #
                for build in os.listdir(dirRun):
                    dirBuild = os.path.join(dirRun, build)
                    if os.path.isdir(dirBuild):
                        runs[run][build] = {}

                        # -- Count Users --- #
                        numUsers = 0
                        for user in os.listdir(dirBuild):
                            dirUser = os.path.join(dirBuild, user)
                            if os.path.isdir(dirUser):
                                numUsers += 1

                        
                        hasOpData = False

                        sessionStats = {}
                        #init sessionStats
                        intervals = int(round(duration / window_length))
                        sessions = set(sessionIds)
                        for session in sessions:
                            sessionStats.setdefault(session, [0L]*intervals)

                        # -- Users --- #
                        for user in os.listdir(dirBuild):
                            session = sessionIds[int(user)]
                            work = sessionStats[session]
                                          
                            dirUser = os.path.join(dirBuild, user)
                            if os.path.isdir(dirUser):
                                if not os.path.isfile(os.path.join(dirUser, "transactions.log")):
                                    print "WARNING: no transaction log found in %s!" % dirUser
                                    continue
                                for rawline in open(os.path.join(dirUser, "transactions.log")):

                                    linedata = rawline.split(";")
                                    if len(linedata) < 2:
                                        continue

                                    starttime   = float(linedata[2])*1000
                                    if len(linedata) > 3:
                                        opData = ast.literal_eval(linedata[3])
                                        for op in opData:
                                            opEndTime = float(op["endTime"])
                                            opDuration = long(op["duration"])
                                            #calculate index in work array
                                            combinedEndTime = int(opEndTime + starttime)
                                            index = int(combinedEndTime/window_length)
                                            if(index < intervals):
                                                work[index] += opDuration
                            runs[run][build] = {"sessionStats": sessionStats}
        return runs