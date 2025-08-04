# BA_Digital_Twin_Mueller_Thavalingam

## Für Flutter 
Um Dependencies zu Updaten.
Gehe in Frontent Ordner und führe in CMD "flutter pub get"

## Für Docker neu:

### Wenn im Frontend und Backend etwas geändert wurde aber Datenbank nicht gelöscht werden soll
docker-compose down
docker-compose up --build


### wenn datenbank gelöscht werden loss
docker-compose down -v
docker-compose up --build



### Website
http://160.85.255.184:8080

http://160.85.255.184:8000/get-a-records?domain=igs-gmbh.ch

## Für Docker alt:
docker images -> show all images
docker ps -> show all running containers
docker ps -a -> show all containers

docker rm ["name"] -> delete container
docker image rm ["name"] -> delete image

docker build -t [python_ip_adress] . -> build image from Dockerfile and Scripts
docker run --name [ip_adress] [python_ip_adress] -> build Container [ip_adress] from image

docker restart ip_adress -> restart finished container
docker logs ip_adress -> show all logs from container

