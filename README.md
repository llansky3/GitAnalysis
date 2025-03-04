# GitAnalysis
## Idea
The  Git Commit Analysis is based on 3 simple ideas:

* Unavoidable altering lines in the codes leads to software bugs and thus creating a risk. This of course unavoidable if we want to be adding new features and fixing bugs.
* Each software bug needs certain time (project dependent) to be uncovered and fixed. Therefore a given software version (feature set) needs time to stabilize.
* One should avoid using features that has not through this period of "stabilization" unless they are absolutely must haves and worth the risk.

<img src="docs/stabilization period of faults after release.png" alt="Stabilization period of faults after release" width="60%" height="60%">

## How to run analysis on a Git repository
1. Checkout any repository to a [FOLDER]
2. Gather commits information in CSV file by:
```console
gitlogs2csv.sh [FOLDER]
```
3. The (2) will create output.csv (in the data folder)
```console
GITLOG2CSV
Processing repository in directory: [FOLDER]
┏━━━━━
┣ getting git tags ... done (184 tags)
┣ exporting git history to data/output.csv ... done
┻
```
4. Run analysis by: 
```console
python3 run_analysis.py
```
## Results
In the example results below section you can 2 plots:
*  Cumulative sum of lines altered
    * Lines altered = lines added + lines deleted
    * Note that this weights more the changed lines as they are counted twice (changed line = 1 line deleted + 1 line added). But even weighted approach doesn't change the conclusion much.
* Cumulative normalized fault score
    * Using parameter and assuming that after 180 days, 5% bugs are left and the number of bugs decreases exponentially. This it tunable parameter of the script.
    * Then cumulative fault score is just adding up the residuals of bugs from given commits
    * For example: in commit A, 100 lines were changed and in 180 days the 5% of bugs will be left, thus 5 lines in case that all the lines would be buggy. This doesn't assume how many buggy lines are in these 100 lines. Just adds up the speed of changes to evaluate the risk.
    * This number of buggy lines and speed of fixing of course vary among project and even with project phase. This doesn't consider that at all.

## Example output for jemalloc project
<img src="docs/Example output - Figure_1  - jemalloc.png" alt="Example output for jemalloc project">

```console
GIT ANALYSIS
┏━━━━━
┣ loaded 3545 commits from data/output.csv
```
## Experimental mode
To run different experimental main with different features:
```console
python3 run_analysis.py --experimental
```


