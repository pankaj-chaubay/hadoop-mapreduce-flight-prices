#!/usr/bin/env bash
# Upload the data to HDFS and run the job on YARN with Hadoop Streaming.
# Usage: bash scripts/run_hadoop.sh data/flight_prices.csv
set -euo pipefail

INPUT_FILE=${1:?path to the CSV file}
HDFS_IN=/user/$USER/flights/input
HDFS_OUT=/user/$USER/flights/output
STREAMING_JAR=$(ls "$HADOOP_HOME"/share/hadoop/tools/lib/hadoop-streaming-*.jar | head -1)

hdfs dfs -mkdir -p "$HDFS_IN"
hdfs dfs -put -f "$INPUT_FILE" "$HDFS_IN/"
hdfs dfs -rm -r -f "$HDFS_OUT"

# The whole "TASK|key" string is the key (text before the first tab), so Hadoop
# sorts and partitions on it. The same script runs as combiner and reducer.
hadoop jar "$STREAMING_JAR" \
  -D mapreduce.job.name="flight-price-analysis" \
  -D mapreduce.job.reduces=2 \
  -files mapreduce/mapper.py,mapreduce/reducer.py \
  -mapper "python3 mapper.py" \
  -combiner "python3 reducer.py" \
  -reducer "python3 reducer.py --final" \
  -input "$HDFS_IN" \
  -output "$HDFS_OUT"

hdfs dfs -cat "$HDFS_OUT"/part-* | sort > results/output_hadoop.tsv
echo "Result: results/output_hadoop.tsv ($(wc -l < results/output_hadoop.tsv) rows)"
echo "Job history: http://localhost:8088"
