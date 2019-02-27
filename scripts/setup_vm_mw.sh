#!/bin/bash
sudo apt-get update -y
sudo apt-get install htop -y
sudo apt-get install dstat -y
sudo apt-get install git unzip ant openjdk-8-jdk -y
wget https://github.com/RedisLabs/memtier_benchmark/archive/master.zip
unzip master.zip
cd memtier_benchmark-master
sudo apt-get install build-essential autoconf automake libpcre3-dev libevent-dev pkg-config zlib1g-dev -y
autoreconf -ivf
./configure
make
cd
sudo cp memtier_benchmark-master/memtier_benchmark /usr/bin/
