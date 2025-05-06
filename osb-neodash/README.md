# Configuration of Neodash for OpenStudyBuilder

In the folder osb-neodash, you'll find the necessary files that have to be used for building a neodash Docker image for having a personalized logo while the visualizationof dashboards in Neodash.

These files have to replace the same files which are in the public repository of Neodash after its clone from Github. This is done by executing the commands in the lines from 13-17 in the Dockerfile.

These steps include adding the image you want for logo, making the necessary configurations in the JSON file & applying some CSS styling.

The image to be built is in the Dockerfile, where at first we pull the public repository of Neodash, replace the files in the folder "osb-neodash" with the ones that come from public repository & then proceed building the docker image.

