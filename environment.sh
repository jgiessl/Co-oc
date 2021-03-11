#! /bin/bash

flag="$1"

case ${flag} in
	-d|--display)
		docker run --name co-oc_env_cont -v "co-oc_storage:/usr/src/app/data" co-oc:0.0 environment_process.py -d
		docker rm co-oc_env_cont
		;;
	-r|--remove)
		key="$2"
		docker run --name co-oc_env_cont -v "co-oc_storage:/usr/src/app/data" co-oc:0.0 environment_process.py -r ${key}
		docker rm co-oc_env_cont
		;;
	-R|--RemoveAll)
		docker run --name co-oc_env_cont -v "co-oc_storage:/usr/src/app/data" co-oc:0.0 environment_process.py -R
		docker rm co-oc_env_cont
		;;
	-a|--add)
		path_to_file="$2"
		filename="${path_to_file##*/}"
		input_mnt="${path_to_file}:/usr/data/${filename}"
		docker run --name co-oc_env_cont -v "co-oc_storage:/usr/src/app/data" \
			-v ${input_mnt} co-oc:0.0 environment_process.py -a /usr/data/${filename}
		docker rm co-oc_env_cont
		;;
  
	-A|-AddAll)
		path_to_col="$2"
		inputt_mnt="${path_to_col}:/usr/data"
		docker run --name co-oc_env_cont -v "co-oc_storage:/usr/src/app/data" \
			-v "${inputt_mnt}" co-oc:0.0 environment_process.py -A /usr/data
		docker rm co-oc_env_cont
		;;
	-i|--import)
		path_to_file="$2"
		filename="${path_to_file##*/}"
		input_mnt="${path_to_file}:/usr/data/${filename}"
		docker run --name co-oc_env_cont -v "co-oc_storage:/usr/src/app/data" \
		       -v "${input_mnt}" co-oc:0.0 environment_process.py -i /usr/data/${filename}
		docker rm co-oc_env_cont 
		;;	
esac
