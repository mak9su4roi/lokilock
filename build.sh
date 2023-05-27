#! /bin/bash

IMAGES="base_images"

cd ${IMAGES}

while read -r image_name; do
    cd ${image_name}
    echo "<${image_name}>"
    docker build  -t "${image_name}" .
    cd ..
done < <(ls -1)
