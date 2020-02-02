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
    grep '[A-Z].*=' $raw_file || true
        # if [[ "$file" == "TekkenBotPrime.py" && "$func" == "flush" ]]; then continue; fi
        # if [[ "$file" == "MovelistParser.py" && "$func" == "__getstate__" ]]; then continue; fi
        # count=`count_matches $func` || (echo $func && exit 1)
        # if [[ $count -lt 2 ]]; then
        #     echo "$file $func"
        # fi
    # done
}

for raw_file in $raw_files; do
    find_unused $raw_file
done
