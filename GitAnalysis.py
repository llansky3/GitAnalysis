import csv
import time
import datetime
import numpy as np


import matplotlib 
matplotlib.use("TkAgg")
import matplotlib.pyplot as matplt

class GitCommit():
    fields = ['commit_id','author','date','changed_files','lines_added','lines_deleted','tag']
    def __init__(self, r):
        self.values = {}
        for idx, x in enumerate(self.fields):
            self.values[x] = r[idx]
    
    @property
    def timestamp(self):
        t = time.mktime(datetime.datetime.strptime(self.values["date"], '%Y-%m-%d %H:%M:%S').timetuple())
        return t/(3600*24)

    @property
    def lines_altered(self):
        return int(self.values["lines_added"]) + int(self.values["lines_deleted"])

    @staticmethod
    def get_fields():
        return ",".join(GitCommit.fields) 

class GitAnalysis():
    def __init__(self, name):
        print('GIT ANALYSIS')
        print('┏━━━━━')
        self.name = name
        self.commits = []

    def __del__(self):
        print('┻')

    def import_csv(self, fn):
        with open(fn, 'r') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=",")
            header = next(csv_reader)
            if not GitCommit.get_fields() == ",".join(header):
                raise Exception(f'CSV fields in {fn} do not match! Please check the CSV file!\n{GitCommit.get_fields()}\n{",".join(header)}')
            line_count = 0
            for row in csv_reader:
                self.commits.append(GitCommit(row))
                line_count += 1
            print(f'┣ loaded {line_count} commits from {fn}')

    def plot2(self, attr):
        x = self.commits[0]
        t = x.timestamp
        print(t) 

    def plot(self, attr):
        t = []
        y = []
        tags = [];
        for c in self.commits:
            t.append(c.timestamp)
            y.append(c.lines_altered)
            tags.append(c.values["tag"])

        t = np.array(t)
        y = np.array(y)
        idx = np.argsort(t)
        t = t[idx]
        y = y[idx]
        t = t - t[0]
        y = np.cumsum(y)
        y = y - y[0]

        [fig, ax] = matplt.subplots()
        ax.plot(t, y, linewidth=2.0)
        matplt.grid(True)

        [is_at_steady_state, idx_ranges] = GitAnalysis.findSteadyState(t, y, 180, 0.005)
        
        stable_release = False
        stable_release_region = False
        stable_releases = []
        for i, txt in enumerate(tags):
            for rng in idx_ranges:
                if i >= rng[0] and i <= rng[1]:
                    stable_release_region = True
                    break
            else:
                stable_release_region = False
                if stable_release:
                    stable_release = False
                    matplt.setp(last_annotation,color='red')
                    matplt.setp(last_axvline,color='red')
                    stable_releases.append(last_txt)
            if txt:
                last_annotation = ax.annotate(txt, (t[i], 0.95*y[i]), color='gray')
                last_axvline = ax.axvline(t[i], linestyle=':', color='gray', linewidth=0.5)
                last_txt = txt
                if stable_release_region:
                    stable_release = True
                
        else:
            if stable_release:
                matplt.setp(last_annotation,color='red')
                matplt.setp(last_axvline,color='red')
                stable_releases.append(last_txt)

        ax.plot(t[is_at_steady_state], y[is_at_steady_state], 'ro')
        for rng in idx_ranges:
            ax.axvspan(t[rng[0]], t[rng[1]], color='red', alpha=0.2)
        
        dt_start = self.commits[0].values["date"]
        matplt.title(f'Git Commit Analysis: {self.name}')
        ax.set_xlabel(f'Days since {dt_start}')
        ax.set_ylabel('Cummulative sum of altered lines of code [-]')
        matplt.show()

        print('Stable releases')
        for stable_release in stable_releases:
            print(f'{stable_release}')

    @staticmethod
    def findSteadyState(t, sig, min_dt, relative_band):
        n = t.size
        is_sig_at_steady_state = np.full(n, False)
        idx_ranges = []
        idx_start = 0
        while idx_start < n:
            dsig = np.absolute(np.subtract(sig[idx_start:],sig[idx_start]))
            band = relative_band * sig[idx_start]
            idx_in_band = np.where(dsig < band)[0]
            if len(idx_in_band) <= 1:
                idx_start = idx_start + 1
                continue
            idx_last_in_band = np.where(np.diff(idx_in_band) > 1)[0]
            if idx_last_in_band.size == 0:
                idx_last_in_band = idx_start + len(idx_in_band) - 1
            else:
                idx_last_in_band = idx_start + idx_last_in_band[0]

            dt = t[idx_last_in_band] - t[idx_start]
            if dt > min_dt:
                is_sig_at_steady_state[idx_start:idx_last_in_band+1] = True
                idx_ranges.append([idx_start, idx_last_in_band])
            idx_start = idx_last_in_band + 1
        return [is_sig_at_steady_state, idx_ranges]

        