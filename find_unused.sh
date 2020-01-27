#!/bin/bash

set -euo pipefail

function count_matches() {
    func="$1"
    grep -r "$func" src | wc -l
}

for raw_file in `find src -name '*.py'`; do
    file=$(basename $raw_file)
    for func in `grep -o 'def [A-Za-z]\+' $raw_file | awk '{print $2}'`; do
        count=`count_matches $func`
        if [[ $count -lt 2 ]]; then
            echo "$file.$func" && exit 1
        fi
    done
done
