from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import json

class Controller(BaseHTTPRequestHandler):
  def sync(self, parent, children):
    # Compute status based on observed state.
    desired_status = {
      "jobs": len(children["Job.batch/v1"])
    }
    # Generate the desired child object(s) with defaults.
    # who = parent.get("spec", {}).get("who", "World")

    # MongoDB
    # <!-- create dump from remote host --> 
    # mongodump --host 10.10.6.203 --port 32668 --db rawdatalabs-ui  --out /tmp/rawdatalabs-ui_dump --username admin --password mongodb 
    # mongorestore --host mongodb --port 27017 --gzip --archive=/backups/  --username admin --password mongodb

    if parent["spec"]["databaseDriver"] == "mongodb":
      mongo_image = "docker.io/centos/mongodb-32-centos7"
      mongo_dump = "mongodump -v --host {service} --port {port} --db {database}  --gzip --archive={backupFilePath} --username {username} --password {password}".format(
        username = parent["spec"]["dump"]["username"],
        password = parent["spec"]["dump"]["password"],
        service = parent["spec"]["dump"]["service"],
        port = parent["spec"]["dump"]["port"],
        database = parent["spec"]["dump"]["database"],
        backupFilePath = parent["spec"]["backupFilePath"]
      )
      mongo_restore = "mongorestore -v --host {service} --port {port} --db {database} --gzip --archive={backupFilePath} --authenticationDatabase={authdb} --username {username} --password {password}".format(
        authdb = parent["spec"]["restore"]["authdb"],
        username = parent["spec"]["restore"]["username"],
        password = parent["spec"]["restore"]["password"],
        service = parent["spec"]["restore"]["service"],
        port = parent["spec"]["restore"]["port"],
        database = parent["spec"]["restore"]["database"],
        backupFilePath = parent["spec"]["backupFilePath"]
      )
      image = mongo_image
      dump = "{mongo_dump} && {mongo_restore}".format(
        mongo_dump = mongo_dump,
        mongo_restore = mongo_restore
      )
    
    # PostgreSQL
    # <!-- create dump from remote host --> 
    # pg_dump -U  $POSTGRESQL_USER -v -d wirecard --format=tar > /tmp/pg_backup/wirecard.tar
    # pg_restore  -h localhost -p 5432 -U postgres -d  wirecard -v /tmp/wirecard.tar 

    elif parent["spec"]["databaseDriver"] == "postgresql":
      pg_image = "docker.io/centos/postgresql-95-centos7"
      pg_dump = "pg_dump --dbname=postgresql://{username}:{password}@{service}:{port}/{database} -v -h {service} -p {port} --format={backupFormat} -f {backupFilePath}".format(
        username = parent["spec"]["dump"]["username"],
        password = parent["spec"]["dump"]["password"],
        service = parent["spec"]["dump"]["service"],
        port = parent["spec"]["dump"]["port"],
        database = parent["spec"]["dump"]["database"],
        backupFormat = parent["spec"]["backupFormat"],
        backupFilePath = parent["spec"]["backupFilePath"]
      )
      pg_restore = "pg_restore --dbname=postgresql://{username}:{password}@{service}:{port}/{auth_db} -v -C -h {service} -p {port} --format={backupFormat}  {backupFilePath}".format(
        username = parent["spec"]["restore"]["username"],
        password = parent["spec"]["restore"]["password"],
        service = parent["spec"]["restore"]["service"],
        port = parent["spec"]["restore"]["port"],
        auth_db = parent["spec"]["restore"]["auth_db"],
        backupFormat = parent["spec"]["backupFormat"],
        backupFilePath = parent["spec"]["backupFilePath"],
        # optional - not used yet
        database = parent["spec"]["restore"]["database"]
      )
      image = pg_image
      dump = "{pg_dump} && {pg_restore}".format(
        pg_dump = pg_dump,
        pg_restore = pg_restore
      )

    desired_pods = [
      {
        "apiVersion": "batch/v1",
        "kind": "Job",
        "metadata": {
          "name": parent["metadata"]["name"]
        },
        "spec": {
          "template": {
            "spec": {
              "volumes": [
                {
                  "name": "tmp",
                  "emptyDir": {}
                }
              ],
              "containers": [
                {
                  "name": "export-pod",
                  "image": image,
                  "volumeMounts": [
                    {
                      "name": "tmp",
                      "mountPath": "/tmp"
                    }
                  ],
                  "command": [
                    "bash",
                    "-c",
                    dump
                  ]
                }
              ],
              "restartPolicy": "OnFailure"
            }
          },
          "backoffLimit": 4
        }
      }
    ]

    return {"status": desired_status, "children": desired_pods}

  def do_POST(self):
    # Serve the sync() function as a JSON webhook.
    observed = json.loads(self.rfile.read(int(self.headers.getheader("content-length"))))
    desired = self.sync(observed["parent"], observed["children"])

    self.send_response(200)
    self.send_header("Content-type", "application/json")
    self.end_headers()
    self.wfile.write(json.dumps(desired))

HTTPServer(("", 80), Controller).serve_forever()