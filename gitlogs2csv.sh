#! /bin/bash

OUTFILE="data/output.csv"

# Input checks
if [ $# -eq 0 ]
then
    echo "Error: No arguments supplied! You must provide a checked out GIT repository to be processed!"
    exit 1
fi
GITREPO=$1
echo "GITLOG2CSV" 
echo "Processing repository in directory:" $GITREPO
echo "┏━━━━━"
if [ ! -d $GITREPO ]; then
    echo "┣ Error: Provided directory doesn't exist!"
    echo "┻"
    exit 1    
fi

original_dir=$(pwd)
cd $GITREPO
if [ ! -d .git ]; then
    echo "┣ Error: Provided directory is not GIT repository!"
    echo "┻"
    cd $original_dir
    exit 1    
fi

# Main
echo -ne "┣ getting git tags ... "
declare -A TAGS
for TAG in $(git tag) ; do
    
    COMMIT_ID_RAW=$(git rev-list -n 1 $TAG)
    # 10
    COMMIT_ID=$(echo $COMMIT_ID_RAW | cut -c1-10)
    TAGS[$COMMIT_ID]=$TAG
    # 9
    COMMIT_ID=$(echo $COMMIT_ID_RAW | cut -c1-9)
    TAGS[$COMMIT_ID]=$TAG
    # 8 
    COMMIT_ID=$(echo $COMMIT_ID_RAW | cut -c1-8)
    TAGS[$COMMIT_ID]=$TAG
    # 7
    COMMIT_ID=$(echo $COMMIT_ID_RAW | cut -c1-7)
    TAGS[$COMMIT_ID]=$TAG
done
echo "done (${#TAGS[@]} tags)"


echo -ne "┣ exporting git history to $OUTFILE ... "
OUTFILE="$original_dir/$OUTFILE"
echo "commit_id,author,date,changed_files,lines_added,lines_deleted,tag" > $OUTFILE 
git log --all --shortstat --reverse --date=local --date=format-local:'%Y-%m-%d %H:%M:%S' --pretty="@%h,%an,%ad," \
    | tr "\n" " " | tr "@" "\n" | while read LINE; do
    if ! [[ $LINE =~ " files changed" ]] && ! [[ $LINE =~ " file changed" ]]; then
        LINE="$LINE 0 file changed, 0 insertion(+), 0 deletion(-)"
    fi

    if ! [[ $LINE =~ " insertions(+)" ]] && ! [[ $LINE =~ " insertion(+)" ]]; then
        if [[ $LINE =~ " file changed" ]]; then
            LINE=$(echo $LINE | sed "s/ file changed/ file changed, 0 insertion(+)/g")
        else
            LINE=$(echo $LINE | sed "s/ files changed/ files changed, 0 insertion(+)/g")
        fi
    fi

    if ! [[ $LINE =~ " deletions(-)" ]] && ! [[ $LINE =~ " deletion(-)" ]]; then
        LINE="$LINE, 0 deletion(-)"
    fi

    # Tags
    COMMIT_ID=$(echo $LINE | sed "s/,.*//")
    if ! [ -z "$COMMIT_ID" ]; then
        LINE="$LINE,${TAGS[$COMMIT_ID]}"
    else
        LINE="$LINE,"
    fi

    if [[ $(echo $LINE | tr -cd , | wc -c) == 6 ]]; then
        # Output only good lines = 7 fields
        echo $LINE >> $OUTFILE
    fi
done

declare -a arr=(" files changed" " file changed" " insertions(+)" " insertion(+)" " deletions(-)" " deletion(-)")

for i in "${arr[@]}"
do
   sed -i "s/$i//g" $OUTFILE
done

echo "done"
# Clean up
cd $original_dir
echo "┻" 


 
#>> 
#  '%s'
#    --date=format-local:'%Y-%m-%d %H:%M:%S' \
# --pretty="%x40%h%x2C%an%x2C%ad%x2C%x22%s%x22%x2C"