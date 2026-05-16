#!/bin/bash
set -e

if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ] || [ -z "$4" ]; then
  echo "Usage: $0 <prd-file> <tasks-file> <progress-file> <iterations>"
  exit 1
fi

PRD_FILE="$1"
TASKS_FILE="$2"
PROGRESS_FILE="$3"
ITERATIONS="$4"

for ((i=1; i<=ITERATIONS; i++)); do
  result=$(ccr code --dangerously-skip-permissions --output-format text --verbose -p \
  "The PRD can be found here: @${PRD_FILE}
  The task list can be found here: @${TASKS_FILE} \
  The progress file can be found here: @${PROGRESS_FILE} \
  1. Based on the progress file and the task list, identify the next task to implement. \
  2. Consult the PRD for acceptance criteria, design decisions, and constraints relevant to that task. \
  3. Implement the task. \
  4. Run your tests and type checks. \
  5. Write a delta to the progress file (signatures, decisions, drift). \
  ONLY WORK ON A SINGLE TASK. \
  Only when all tasks have been completed, output <promise>COMPLETE</promise>.")

  echo "Result: $result"

  if [[ "$result" == *"<promise>COMPLETE</promise>"* ]]; then
    echo "PRD complete after $i iterations."
    exit 0
  fi
done

echo "PRD not complete after $ITERATIONS iterations."
exit 1