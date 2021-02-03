#!/bin/bash

flag="$1"

case ${flag} in
	-c|--continue)
		path_to_col="$2"
		input_mnt="${path_to_col}:/usr/data"
		docker run --name co-oc_train_cont -v "co-oc_storage:/usr/src/app/data" \
			-v ${input_mnt} co-oc:0.0 training.py -c /usr/data
		docker rm co-oc_train_cont
		;;
	-n|--new)
		path_to_col="$2"
		inputt_mnt="${path_to_col}:/usr/data"
		docker run --name co-oc_train_cont -v "co-oc_storage:/usr/src/app/data" \
			-v "${inputt}" co-oc:0.0 training.py -n /usr/data
		docker rm co-oc_train_cont
		;;
esac
