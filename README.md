### DbMigrator-Operator  ###
- Universal Database Migration - quick and easy using DbMigrator Operator.


- Requires : [Metacontroller](https://metacontroller.app/) to be installed on the Kubernetes cluster.




This Operator extends the Kubernetes cluster with an additional Custom Resource from ***rawdatalabs.cloud/v1***, called *ExportJob*; This CRD type, creates an OnDemand Database Transfer, through native Kubernetes *Job*  type pods, exporting contents of different *Databases* between Namespaces or external hosts.



###  Steps to start an ExportJob:

```sh 
#   Create Components.
[Openshift]
▶ oc create -f export-mongo-dev.yaml

[Kubernetes]
▶ kubectl create -f export-mongo-dev.yaml
```

[export-mongo-dev.yaml]
```sh
apiVersion: rawdatalabs.cloud/v1
kind: ExportJob
metadata:
  name: export-mongo-dev
spec:
  backupFilePath: /tmp/archive.gz
  databaseDriver: mongodb
  dump: 
    service: mongodb.development.svc
    port: "27017"
    database: rawdata-dev
    username: rawdata-dev
    password: rawdata-dev
  restore: 
    service: mongodb.devtest.svc
    port: "27017"
    authdb: admin
    database: rawdata-dev
    username: admin
    password: mongodb

```

Please check out the ./export folder for more *ExportJob* examples. 
#### Thanks for reading!  ####