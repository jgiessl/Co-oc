#!/bin/bash

if [ $# -eq 2 ]; then 
	input="$1"
	inputt="$2"
	foldername="${input##*/}"
	savepath="/usr/data/${foldername}"
	docker run --name co-oc_clust \
	       -v "${input}:${savepath}" \
	       -v "${inputt}:/usr/src/app/plots" \
	       co-oc_cluster:0.0 \
	       cluster.py "${savepath}"
	docker rm co-oc_clust

elif [ $# -eq 4 ]; then
	input="$3"
	inputt="$4"
	option="$1"
	number="$2"
	foldername="${input##*/}"
	savepath="/usr/data/${foldername}"
	case ${option} in
		-t|--top_k)
		docker run --name co-oc_clust \
			-v "${input}:${savepath}" \
			-v "${inputt}:/usr/src/app/plots" \
			co-oc_cluster:0.0 \
			cluster.py "${savepath}" "${option}" "${number}"
		docker rm co-oc_clust
	;;
        esac
else
	echo './cluster.sh path/to/dataset path/to/save <-t number>'
fi

