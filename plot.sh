#!/bin/bash

input="$1"
inputt="$2"
filename="${input##*/}"
savepath="/usr/data/${filename}"
docker run --name co-oc_plot \
	-v "${input}:${savepath}" \
	-v "${inputt}:/usr/src/app/ranking_plots" \
	co-oc_plotter:0.0 plotter.py ${savepath}
docker rm co-oc_plot

