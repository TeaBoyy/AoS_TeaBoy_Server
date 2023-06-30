#!/bin/bash

sudo docker run -d -u root -v $(dirname $pwd):/home/container -p 32887:32887/tcp -p 32887:32887/udp -i -t hcgcloud/pterodactyl-images:ubuntu-wine ./hosting_utils/run.sh