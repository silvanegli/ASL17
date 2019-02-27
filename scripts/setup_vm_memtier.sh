#!/bin/bash
sudo apt-get update -y
sudo apt-get install htop -y
sudo apt-get install iperf -y
#sudo apt-get install memcached -y
sudo apt-get install dstat -y
#sudo service memcached stop
sudo apt-get install unzip build-essential autoconf automake libpcre3-dev libevent-dev pkg-config zlib1g-dev -y
wget https://github.com/RedisLabs/memtier_benchmark/archive/master.zip
unzip master.zip
cd memtier_benchmark-master
autoreconf -ivf
./configure
make
cd
sudo cp memtier_benchmark-master/memtier_benchmark /usr/bin/
