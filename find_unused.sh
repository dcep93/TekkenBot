#!/bin/bash

set -euo pipefail

raw_files=`find src -name '*.py'`

function count_matches() {
    func="$1"
    grep "\b$func\b" $raw_files | wc -l
}

function find_unused() {
    raw_file="$1"
    file=$(basename $raw_file)
    for func in `grep -o 'def [A-Za-z_0-9]\+' $raw_file | awk '{print $2}'`; do
        if [[ "$file" == "TekkenBotPrime.py" && "$func" == "flush" ]]; then continue; fi
        if [[ "$file" == "MovelistParser.py" && "$func" == "__getstate__" ]]; then continue; fi
        count=`count_matches $func` || (echo $func && exit 1)
        if [[ $count -lt 2 ]]; then
            echo "$file $func"
        else
            echo $func keep
        fi
    done
}

for raw_file in $raw_files;
    find_unused raw_file
done
