# icough

## Build the Frontend and Backend using Docker Compose

### Build and run:

```
make up
```

### Stop Containers

```
make stop
```

### Clean Containers, Images, Volumes, etc

```
make clean
```

## Build the Frontend using Docker

```
cd icough-app
```

### Build image:

```
docker build -f Dockerfile -t icough-front-img .
```

### Build container:

```
docker run -d -p 4444:3000 --name icough-front --restart always icough-front-img
```

## Build the Backend using Docker

```
cd icough-back
```

### Build image:

```
docker build -f Dockerfile -t icough-back-img .
```

### Build container:

```
docker run -d -p 8888:8000 --name icough-back --restart always icough-back-img
```
