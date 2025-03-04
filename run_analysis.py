import matplotlib 
matplotlib.use("TkAgg")
import matplotlib.pyplot as matplt

import numpy as np
import statistics
import pickle
import math
import argparse

from GitAnalysis import *

def parse_args():
    parser = argparse.ArgumentParser(
        __file__, description="Python script for Git commit history analysis"
    )
    parser.add_argument(
        "--experimental", 
        help="Run different experimental main",
        dest="experimental",
        action="store_true",
        default=False
    )
    return parser.parse_args()

def main_experimental(args):
    print("GIT ANALYSIS - MAIN EXPERIMENTAL")
    test = GitCommit2('./tests/clones/jemalloc/')
    # test = GitCommit2('./../fitness_scoring/cryptsetup/')
    # test = GitCommit2('./../fitness_scoring/git-log-testing/')
    # test.get_altered_lines('c7805f1e')
    # test.get_altered_lines('f7436907')
    commits = test.get_all_commits()
    tags = test.get_all_tags()
    print(commits[0]['id'])
    # dt_start = commits[0].values["date"]
    datafile = 'jemalloc.data'
    # datafile = 'cryptsetup.data'
    # altered_lines = test.get_altered_lines(commit_ids[0])

    [stats, tracker_history] = test.track(commits, tags)

    with open(datafile, 'wb') as f:
        pickle.dump([stats, tracker_history], f)

    # with open(datafile, 'rb') as f:
    #     [stats, tracker_history] = pickle.load(f)

    tmin = min([x['timestart'] for x in stats])
    tmax = max([x['timeend'] for x in stats])

    tstep = 24*3600*30

    tx = range(math.floor(tmin), math.floor(tmax), tstep)
    ty = []
    y = []
    for t in tx:
        tspans = []
        for i, s in enumerate(stats):
            if t > s['timeend']:
                del stats[i]
            elif t >= s['timestart'] and t <= s['timeend']:
                if s['timespan'] >= 0:
                    tspans.append(s['timespan'])
        if tspans:    
            ty.append(t/24/3600)
            y.append(statistics.median(tspans)/24/3600)     


    [fig, ax] = matplt.subplots()
    ax.plot(ty, y, linewidth=2.0)

    matplt.grid(True)

    matplt.show()
    ax.set_xlabel(f'Timestamps since beginning of the project')
    ax.set_ylabel(f'Median time to fix code [days] ')
    print('-- end --')
    # alfa = -1.0 * np.log(0.05) / 180 
    # print(GitAnalysis.exponential(180, alfa))

    # # count, bins, ignored = plt.hist(np.random.weibull(5.,1000))
    # xs = np.arange(0.,2000.)/10.
    # # scale = count.max()/GitAnalysis.weibull(x, 1, 1).max()
    # y = []
    # for x in xs:
    #     y.append(GitAnalysis.exponential(x, alfa))
    # matplt.plot(xs, y)
    # matplt.show()

    # x = np.array([1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20])
    # y = np.array([1,14,19,20,21,20,20,19,22,23,20,19,24,21,25,24,25,26,25,24])
    # print("Test")

    # [is_at_steady_state, idx_ranges] = GitAnalysis.findSteadyState(x, y, 2, 3)

    # [fig, ax] = matplt.subplots()
    # ax.plot(x, y, linewidth=2.0)
    # ax.plot(x[is_at_steady_state], y[is_at_steady_state], 'ro')

    # for rng in idx_ranges:
    #     ax.axvspan(x[rng[0]], x[rng[1]], color='red', alpha=0.2)

    # matplt.grid(True)

    # matplt.show()

def main(args):
    package = ''
    analysis = GitAnalysis(package)
    if package:
        analysis.import_csv(f'data/output_{package}.csv')
    else:
        analysis.import_csv('data/output.csv')
    # analysis.plot('lines_altered')
    # analysis.plot(90, 0.005, 'lines_weighted')
    analysis.plot2('lines_altered')

if __name__ == '__main__':
    args = parse_args()
    if args.experimental:
        # WIP: experimental analysis with additional features
        main_experimental(args)
    else:
        # Default analysis
        main(args)
        