#!/bin/bash
set -e

if [ -z "$1" ] || [ -z "$2" ]; then
  echo "Usage: $0 <tasks-file> <iterations>"
  exit 1
fi

TASKS_FILE="$1"
ITERATIONS="$2"

for ((i=1; i<=ITERATIONS; i++)); do
  result=$(claude --dangerously-skip-permissions --output-format text --verbose -p \
  "The PRD can be found here: @plans/prd-video-download-playback.md
  The task list can be found here: @${TASKS_FILE} \
  The progress file can be found here: @progress.txt \
  1. Based on the progress file and the task list, identify the next task to implement. \
  2. Implement the task. \
  3. Run your tests and type checks. \
  4. Write a delta to the progress file (signatures, decisions, drift). \
  ONLY WORK ON A SINGLE TASK. \
  If the task list is complete, output <promise>COMPLETE</promise>.")

  echo "Result: $result"

  if [[ "$result" == *"<promise>COMPLETE</promise>"* ]]; then
    echo "PRD complete after $i iterations."
    exit 0
  fi
done

echo "PRD not complete after $ITERATIONS iterations."
exit 1