# Buildroot Chipsee

⚠️ Currently under construction ⚠️

This repository contains the `external tree` for `Buildroot` to produce images using a minimal configuration aimed to test hardware and software related to Chipsee products.

Please keep in mind that `Buildroot` reads from the environment variable `BR2_EXTERNAL` the path of the folders where it expect to find the types of components like this repository. Info to learn about it here: [`Buildroot` external mechanism][br2_external].

Also, note that the `BR2_EXTERNAL_CHIPSEE_BR_PATH` referenced in the code is built by `Buildroot` using the name provided in the `external.desc` file. Then there is no need to provide it.


In case you're interested:
- Optional use of [a container based implementation of Buildroot][docker_buildroot], that provides a fast and convenient way to start working right away and keep multiple and independent instances for different targets at the same time.
- To manage the above, a Shell script is provided.


[br2_external]:http://buildroot.uclibc.org/downloads/manual/manual.html#outside-br-custom
[docker_buildroot]:https://github.com/vidalastudillo/docker-buildroot
