# BigData_Assignment3

## Setup replicas

1. Open terminal
2. Run command line ```sudo nano /etc/hosts```
3. Paste ```127.0.0.1 mongo1 mongo2 mongo3``` and press ```Ctrl + O```, then ```Enter``` to save. Press ```Ctrl + X``` to exit.
4. In terminal, navigate to the folder where docker-compose.yml is located.
5. Run command line ```docker compose up -d```
6. Execute this code to create replicas:
```
docker exec -it mongo1 mongosh --port 27017 --eval 'rs.initiate({
     _id: "rs0",
     members: [
       {_id: 0, host: "mongo1:27017"},
       {_id: 1, host: "mongo2:27018"},
       {_id: 2, host: "mongo3:27019"}
     ]
   })'
```

## Run project

1. Add csv file inside input folder
2. Open ```main.py``` file inside code fodler
3. Make adjustments if need in options and file sections
4. Run ```main.py``` file.
