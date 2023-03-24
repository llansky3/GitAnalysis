import csv
import time
import datetime
import numpy as np
import subprocess
import re


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

class GitCommit2():
    def __init__(self, path):
        self.path = path

    def get_all_commits(self):
        out = GitCommit2.execute_shell_command(f"""
            cd {self.path} && git log --all --reverse --date=local --date=format-local:'%Y-%m-%d %H:%M:%S' --pretty=format:"%h,%an,%ad"
            """)
        commits = []
        for o in out:
            v = o.split(',')
            c = {}
            c['id'] = v[0]
            c['author'] = v[1]
            c['timestamp'] = GitCommit2.timestamp(v[2])
            commits.append(c)
        return commits  

    def get_altered_lines(self, commit_id):
        out = GitCommit2.execute_shell_command(f"""
            cd {self.path} && git show --unified=0 {commit_id} 2>&1
            """)
        # out = '\n'.join(out)    
        # print(f'{out}')
        current_file = ''
        ptrn_file = re.compile(r"""		    
            [\+-][\+-][\+-]\s[a,b]/(?P<file>.*)\s?
            """, re.VERBOSE)

        ptrn_chunk = re.compile(r"""		    
            @@\s-(?P<m_line>\d+),?(?P<m_length>\d*)\s\+(?P<p_line>\d+),?(?P<p_length>\d*)\s@@.*
            """, re.VERBOSE)

        altered_lines = {}
        for o in out:
            match = ptrn_file.match(o)
            if match is not None:
                current_file = match.group("file")
                # print(current_file)
                if not current_file in altered_lines:
                    altered_lines[current_file] = {}
                    altered_lines[current_file]['added'] = []
                    altered_lines[current_file]['deleted'] = []
            elif current_file:    
                match = ptrn_chunk.match(o)
                if match is not None:
                    m_line = int(match.group("m_line"))
                    m_length = match.group("m_length")
                    if not m_length:
                        m_length = 1
                    else:
                        m_length = int(m_length)
                    p_line = int(match.group("p_line"))
                    p_length = match.group("p_length")
                    if not p_length:
                        p_length = 1
                    else:
                        p_length = int(p_length)    

                    deleted_lines = []    
                    for i in range(0, m_length):
                        deleted_lines.append(m_line+i)
                    if deleted_lines:
                        altered_lines[current_file]['deleted'] += deleted_lines    

                    added_lines = []
                    for i in range(0, p_length):
                        added_lines.append(p_line+i)
                    if added_lines:
                        altered_lines[current_file]['added'] += added_lines
                    
        for file in altered_lines:
            altered_lines[file]['added'] = GitCommit2.unique(altered_lines[file]['added'])
            altered_lines[file]['deleted'] = GitCommit2.unique(altered_lines[file]['deleted'])
            altered_lines[file]['deleted'].sort(reverse=True) 
                          
        return altered_lines
    
    def track(self, commits):
        tracker = {}
        tracker_history = {}
        for c in commits:
            print(c['id'])
            altered_lines = self.get_altered_lines(c['id'])
            for file, v in altered_lines.items():
                print(file)
                if not file in tracker:
                    tracker[file] = {}
                    tracker[file]['lines'] = ['N/A']
                for i in v['deleted']:
                    if i:
                        removed = tracker[file]['lines'].pop(i)
                        timespan = c['timestamp'] - tracker_history[removed]['timestamp']
                        print(f'Line {i} from commit {removed} removed! Lasted {timespan/3600/24} days!')  
                for i in v['added']:
                    if i:
                        tracker[file]['lines'].insert(i, c['id'])
            tracker_history[c['id']] = {}
            tracker_history[c['id']]['timestamp'] = c['timestamp']
            tracker_history[c['id']]['tracker'] = tracker

        return tracker_history

    @staticmethod
    def execute_shell_command(cmd):
        # Shell executes given command
        try:
            r = subprocess.check_output(cmd, shell=True)
        except subprocess.CalledProcessError as e:
            r = e.output 
        r = r.decode('UTF-8','ignore').split("\n")
        return r 

    @staticmethod
    def timestamp(date):
        return time.mktime(datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S').timetuple())

    @staticmethod
    def unique(a):
        return list(set(a))       

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
        