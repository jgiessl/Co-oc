#!/bin/bash

cd storage
docker build -t co-oc_store:0.0 .
cd ..
docker build -t co-oc:0.0 .
docker run --name co-oc_stor -v co-oc_storage:/data co-oc_store:0.0
docker stop co-oc_stor
