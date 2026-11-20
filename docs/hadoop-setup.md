# Single-node Hadoop setup

Steps for a pseudo-distributed cluster on Ubuntu (or WSL2 on Windows). This is the setup the assignment asked for: HDFS and YARN running, web interfaces on ports 9870 and 8088.

## 1. Java and SSH

```bash
sudo apt update && sudo apt install -y openjdk-11-jdk ssh pdsh
ssh-keygen -t rsa -P "" -f ~/.ssh/id_rsa
cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
ssh localhost exit        # must work without a password
```

## 2. Hadoop

```bash
wget https://downloads.apache.org/hadoop/common/hadoop-3.3.6/hadoop-3.3.6.tar.gz
tar xzf hadoop-3.3.6.tar.gz && sudo mv hadoop-3.3.6 /opt/hadoop
cat >> ~/.bashrc <<'EOF'
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export HADOOP_HOME=/opt/hadoop
export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin
export PDSH_RCMD_TYPE=ssh
EOF
source ~/.bashrc
echo "export JAVA_HOME=$JAVA_HOME" >> $HADOOP_HOME/etc/hadoop/hadoop-env.sh
```

## 3. Configuration

`$HADOOP_HOME/etc/hadoop/core-site.xml`

```xml
<configuration>
  <property><name>fs.defaultFS</name><value>hdfs://localhost:9000</value></property>
</configuration>
```

`hdfs-site.xml` (one node, so one copy of each block)

```xml
<configuration>
  <property><name>dfs.replication</name><value>1</value></property>
</configuration>
```

`mapred-site.xml`

```xml
<configuration>
  <property><name>mapreduce.framework.name</name><value>yarn</value></property>
  <property><name>mapreduce.application.classpath</name>
    <value>$HADOOP_HOME/share/hadoop/mapreduce/*:$HADOOP_HOME/share/hadoop/mapreduce/lib/*</value></property>
</configuration>
```

`yarn-site.xml`

```xml
<configuration>
  <property><name>yarn.nodemanager.aux-services</name><value>mapreduce_shuffle</value></property>
  <property><name>yarn.nodemanager.env-whitelist</name>
    <value>JAVA_HOME,HADOOP_COMMON_HOME,HADOOP_HDFS_HOME,HADOOP_CONF_DIR,CLASSPATH_PREPEND_DISTCACHE,HADOOP_YARN_HOME,HADOOP_HOME,PATH,LANG,TZ,HADOOP_MAPRED_HOME</value></property>
</configuration>
```

## 4. Start and check

```bash
hdfs namenode -format
start-dfs.sh
start-yarn.sh
jps          # NameNode, DataNode, SecondaryNameNode, ResourceManager, NodeManager
```

* HDFS: http://localhost:9870
* YARN: http://localhost:8088

## 5. Data and job

```bash
python scripts/make_sample.py data/big.csv --megabytes 1100   # 1 GB+ test file, if you have no real data of that size
bash scripts/run_hadoop.sh data/big.csv
```

The job shows up in the YARN web interface while it runs. The counters `FlightPrices:good_row`, `bad_row` and `bad_date` in the job summary show how many rows were used and skipped.

## Stop

```bash
stop-yarn.sh && stop-dfs.sh
```
