#!/bin/bash

# 第一步：重启容器
sudo docker start funasr_server

# 第二步：进入容器
sudo docker exec -it funasr_server /bin/bash