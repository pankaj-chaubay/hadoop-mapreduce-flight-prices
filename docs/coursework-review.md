# Coursework review

**Module:** Big Data Analytics, M.Sc. Data Analytics, BSBI, Term 2 (submitted October 2024)
**Original:** a report (Big Data principles for German health insurance, Hadoop setup steps) and a MapReduce job in a text file. The original mapper and reducer are kept unchanged in [`original/`](../original).

## What the original did

* Task 1 discussed Big Data (the five Vs, HDFS, YARN, MapReduce) for health insurance in Germany.
* Task 2 set up Hadoop 2.9.2 and loaded a medical insurance data set into HDFS.
* Task 3 wrote a Python mapper and reducer for a flight price file with three outputs: average price per airline, route frequency, and price distribution per date. The job was submitted with Hadoop Streaming.

## What I found when I rebuilt it

I ran the original scripts on the same 1,038,803-row flight file.

| Issue | What happened | Fix |
|---|---|---|
| The key was only the task name | Hadoop Streaming treats the text before the first tab as the key. The mapper wrote `AveragePrice<TAB>airline<TAB>price`, so the key was `AveragePrice` and lines for different airlines reached the reducer mixed together. When I passed the mapper output through a key-only sort (as Hadoop does), the reducer printed 817,072 "average price" lines for 12 airlines, each one a partial average. | Key is `TASK|name`, so Hadoop sorts and partitions on the full key |
| Date format did not match the file | The mapper parsed `%d/%m/%Y`, but every date in the file uses dashes (`24-03-2019`). The error was caught after the first two outputs had been printed, so the price distribution produced **no output at all** and the error log had one line per row. | Mapper accepts `/`, `-` and ISO dates; bad dates are counted, not hidden |
| Local test skipped steps | The test command piped the CSV straight into the reducer (`cat file | python reducer.py`), without the mapper and without sorting. | `scripts/local_run.py` runs map, combine, partition, sort and reduce the way Hadoop does, and tests check the result does not change with the number of mappers or reducers |
| No combiner | Every mapped line crossed the network to the reducers. | The reducer merges sum, count, min and max, so the same script runs as combiner |
| 39% duplicate rows | The flight file had 1,038,803 rows but only 631,011 distinct ones. It looks like the 10,683-row Kaggle file was enlarged to reach the 1 GB requirement, and dates are spread almost evenly across March to June. | Results reported with and without duplicates; `make_sample.py` makes large test files without inflating real data |
| Report and job used different data | The report described a medical insurance data set and the job analysed flight prices. | One data set, described in the README |
| Text encoding | Route arrows (`→`) became `?` in the file. | Route is built from the Source and Destination columns |
| Hadoop command | The submit command ended with a trailing `\` and pointed at Hadoop 2.9.2 paths. | `scripts/run_hadoop.sh` for Hadoop 3, with the streaming jar found from `$HADOOP_HOME` |

## What the corrected job shows

Average price per airline on the original file. Duplicates change the averages by up to 19% (SpiceJet), which is why both are reported.

| Airline | Flights (all rows) | Average (all rows) | Flights (no duplicates) | Average (no duplicates) |
|---|---|---|---|---|
| Jet Airways | 374,280 | 10,661 | 223,411 | 10,819 |
| IndiGo | 199,640 | 7,025 | 112,177 | 8,070 |
| Air India | 170,341 | 9,373 | 110,692 | 9,740 |
| Multiple carriers | 116,312 | 10,120 | 77,142 | 10,028 |
| SpiceJet | 79,532 | 6,239 | 45,002 | 7,433 |
| Vistara | 46,580 | 8,351 | 28,810 | 8,991 |
| Air Asia | 31,014 | 6,817 | 19,627 | 7,482 |

The averages from the corrected job match the original reducer's output once its input is fully sorted, which confirms the arithmetic was right and the problem was the key.
