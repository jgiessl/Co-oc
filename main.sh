#!/bin/bash
input="$1"
inputt="$2"
filename="${input##*/}"
savepath="/usr/data/${filename}"
vol_mnt="co-oc_storage:/usr/src/app/data"
input_mnt="${input}:/usr/data/${filename}"
save_mnt="${inputt}:/usr/src/app/temp_result"
docker run --name co-oc_cont \
	-v ${vol_mnt} \
	-v ${input_mnt} \
	-v ${save_mnt} \
	co-oc:0.0 main_program.py ${savepath}
docker rm co-oc_cont
