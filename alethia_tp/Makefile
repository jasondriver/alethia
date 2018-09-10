all:
	.docker/build.sh

image:
	docker build -t alethia-build .docker/

.PHONY: all image

clean:
	rm -f *.whl
