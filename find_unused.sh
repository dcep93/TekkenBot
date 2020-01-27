#!/bin/bash

set -euo pipefail

raw_files=`find src -name '*.py'`

function count_matches() {
    func="$1"
    grep "$func" $raw_files | wc -l
}

for raw_file in $raw_files; do
    file=$(basename $raw_file)
    for func in `grep -o 'def [A-Za-z]\+' $raw_file | awk '{print $2}'`; do
        count=`count_matches $func`
        if [[ $count -lt 2 ]]; then
            echo "$file.$func"
        fi
    done
done
