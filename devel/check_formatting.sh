#!/bin/bash

for dir in python api_helpers; do

cd $dir

# Start with an exit code of 0 (success)
exit_code=0

# Use process substitution to redirect the output of the find command to a file descriptor
while read file; do
    # Run autopep8 with the --diff option on each file
    diff_output=$(autopep8 "$file" --diff)
    
    # If there's any output from the --diff option, print it and update the exit code
    if [[ ! -z "$diff_output" ]]; then
        echo "autopep8: Changes needed for $file:"
        echo "$diff_output"
        echo "------"
        echo ""
        echo ""
        exit_code=1
    fi
done < <(find . -name '*.py')

cd ..

done

# Exit the script with the appropriate exit code
exit $exit_code