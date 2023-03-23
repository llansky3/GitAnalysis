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

    @property
    def lines_weighted(self):
        added = int(self.values["lines_added"])
        deleted = int(self.values["lines_deleted"])
        changed = np.maximum(added, deleted)
        if added >= deleted:
            added = added - changed
            deleted = 0
        else:
            deleted = deleted - changed
            added = 0
        return 1*changed + 1.5*added + 0.2*deleted 

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

    def plot(self, min_dt, relative_band, attr):
        t = []
        y = []
        tags = [];
        for c in self.commits:
            t.append(c.timestamp)
            y.append(getattr(c, attr))
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

        [is_at_steady_state, idx_ranges] = GitAnalysis.findSteadyState(t, y, min_dt, relative_band)
        
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
        ax.set_ylabel(f'Cummulative sum of {attr}')
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

    @staticmethod
    def weibull(x, alfa, k):
        if x < 0:
            return 0
        else:
            return (k / alfa) * (x / alfa)**(k - 1) * np.exp(-(x / alfa)**k)

    @staticmethod
    def exponential(x, alfa):
        if x < 0:
            return 0
        else:
            return np.exp(-1.0*alfa*x)

    def plot2(self, attr):
        # Parameter - after 180 days, 5% bugs are left
        alfa = -1.0 * np.log(0.05) / 30
        
        t = []
        y = []
        tags = [];
        for c in self.commits:
            t.append(c.timestamp)
            y.append(getattr(c, attr))
            tags.append(c.values["tag"])

        t = np.array(t)
        y = np.array(y)
        idx = np.argsort(t)
        t = t[idx]
        y = y[idx]
        t = t - t[0]
        y = np.cumsum(y)
        y = y - y[0]
        p = np.full(t.size, 0.0)
        for i, t1 in enumerate(t):
            for t2 in t[i:]:
                p[i] = p[i] + y[i]*GitAnalysis.exponential(t2 - t1, alfa)

        # p_norm = (p-np.min(p))/(np.max(p)-np.min(p))
        p_norm = p

        [fig, axs] = matplt.subplots(2)
        axs[0].plot(t, y, linewidth=1.0)
        matplt.grid(True)
        axs[1].plot(t, p_norm, linewidth=1.0)
        matplt.grid(True)
        
        for i, txt in enumerate(tags):
            if txt:
                for ax in axs:
                    last_annotation = ax.annotate(txt, (t[i], 0), color='gray')
                    last_axvline = ax.axvline(t[i], linestyle=':', color='gray', linewidth=0.5)
                axs[0].plot(t[i], y[i], 'x', color = 'red')
                axs[1].plot(t[i], p_norm[i], 'x', color = 'red')
                last_txt = txt

        fig.suptitle(f'Git Commit Analysis: {self.name}')        
        dt_start = self.commits[0].values["date"]
        for ax in axs:
            ax.set_xlabel(f'Days since {dt_start}')
        axs[0].set_ylabel(f'Cummulative sum of {attr}')
        axs[1].set_ylabel(f'Cummulative normalized fault score')
        matplt.show()
        