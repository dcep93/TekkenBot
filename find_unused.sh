#!/bin/bash

set -euo pipefail

raw_files=`find src -name '*.py'`

function count_matches() {
    func="$1"
    grep "\b$func\b" $raw_files | wc -l
}

for raw_file in $raw_files; do
    file=$(basename $raw_file)
    if [[ "$file" == "GameStateGetters.py" ]]; then continue; fi
    for func in `grep -o 'def [A-Za-z_0-9]\+' $raw_file | awk '{print $2}'`; do
        if [[ "$file" == "TekkenBotPrime.py" && "$func" == "flush" ]]; then continue; fi
        count=`count_matches $func` || (echo $func && exit 1)
        if [[ $count -lt 2 ]]; then
            echo "$file $func"
        fi
    done
done
