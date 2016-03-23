## postgres_exporter

#requirement
  ```
  python2.7
  prometheus_client
  psycopg2
```
##RUN
 ```
  python postgresql_exporter.py user=postgres_exporter password={{ some_password }}  \
  host={{ dns_name_master_postgres or ip_address }} dbname={{ name DB }}  \
  dbname_postgres={{ usual it is 'postgres'| default - postgres }}
 ```
