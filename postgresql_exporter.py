#/bin/python

from prometheus_client import start_http_server, Summary
import time
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily, REGISTRY
import psycopg2
import sys

for arg in sys.argv:
	if 'server_port' in arg:
		server_port = int(arg[12:])
	if 'user' in arg :
		user = arg[5:]
	if 'password' in arg:
		password = arg[9:]
	if 'host' in arg:
		host = arg[5:]
	if 'dbname' in arg:
		dbname = arg[7:]
	if 'dbname_postgres' in arg:
		dbname_postgres = arg[16:]
	else:
		dbname_postgres = 'postgres'
	if 'help' in arg:
		print "python prometheus.py user=postgres_exporter server_port={{ some_port }} password={{ some_password }} host={{ dns_name_master_postgres or ip_address }} dbname={{ name DB }} dbname_postgres={{ usual it is 'postgres'| default -postgres }}"
		sys.exit()



# Try to connect
def postgres(host, dbname, user, password):
	conn=psycopg2.connect(host=host, dbname=dbname_postgres, user=user, password=password)
	try:
	    conn=psycopg2.connect(host=host, dbname=dbname_postgres, user=user, password=password)
	except:
	    print "I am unable to connect to the database."
	else:

		cur = conn.cursor()
		db = {}

		try:
		    cur.execute("""SELECT * FROM pg_stat_replication;""")
		except:
		    print "I can't SELECT * FROM pg_stat_replication;"

		rows = cur.fetchall()
		replic_ip = []
		replic_pid = []
		replic_usesysid = []
		replica_lags = []
		replic_status = []
		replic_stat = len(rows)

		db.update({'replic_status': replic_stat})
		
		for row in rows:
			replic_ip.append(row[4])
			replic_pid.append(row[0])
			replic_usesysid.append(row[1])

			try:
			    cur.execute("select greatest(0,pg_xlog_location_diff(pg_current_xlog_location(), replay_location)) from pg_stat_replication where client_addr = %s", (row[4],))
			except:
			    print "I can't select greatest(0,pg_xlog_location_diff(pg_current_xlog_location(), replay_location)) ..."

			rows = cur.fetchall()
			replica_lags.append(float(rows[0][0]))
			
			db.update({'replic_pid': replic_pid, 'replic_usesysid': replic_usesysid, 'replic_ip': replic_ip, 'replica_lags': replica_lags})
	###DB_Size
		
		try:
		    cur.execute("""SELECT pg_database.datname, pg_size_pretty(pg_database_size(pg_database.datname)) AS size FROM pg_database;""")
		except:
		    print "I can't SELECT pg_database.datname, pg_size_pretty(pg_database_size(pg_database.datname)) AS ...."

		rows = cur.fetchall()
		for row in rows:
			if row[0] == dbname:
				db.update({'db_name': row[0], 'db_size': float(row[1][:-2])})
	    
	##Deadlocks
		try:
		    cur.execute("""SELECT sum(deadlocks) from pg_stat_database;""")
		except:
		    print "I can't SELECT deadlocks"

		rows = cur.fetchall()
		for row in rows:
			db.update({'db_deadlocks': float(row[0])})


	###Too many connection 

	# SHOW max_connections;
		try:
		    cur.execute("""select count(*) from pg_stat_activity;""")
		except:
		    print "I can't select count(*) from pg_stat_activity;"

		rows = cur.fetchall()
		for row in rows:
			db.update({'total_connections': float(row[0])})
	###MAX Connection
		try:
		    cur.execute("""SHOW max_connections;""")
		except:
		    print "I can't SHOW max_connections"

		rows = cur.fetchall()
		for row in rows:
			db.update({'max_connections': float(row[0])})

		end_connections = db['max_connections'] - db['total_connections']
		db.update({'left_connections': end_connections})
		
		cur.close()
		conn.close()
		return db

	


# postgres(host, dbname, user, password)
# get_db = postgres(host, dbname, user, password)
# print(get_db)

class CustomCollector(object):
    def collect(self):
        size = CounterMetricFamily('pg_master_data_size', 'size database', labels=['db_name'])
        size.add_metric([get_db['db_name']], get_db['db_size'])
        
        max_connections = CounterMetricFamily('pg_master_max_connections', 'max_connections', labels=['db_name'])
        max_connections.add_metric([get_db['db_name']], get_db['max_connections'])
        
        total_connections = CounterMetricFamily('pg_master_total_connections', 'total_connections', labels=['db_name'])
        total_connections.add_metric([get_db['db_name']], get_db['total_connections'])

        left_connections = CounterMetricFamily('pg_master_left_connections', 'left_connections', labels=['db_name'])
        left_connections.add_metric([get_db['db_name']], get_db['left_connections'])

        db_deadlocks = CounterMetricFamily('pg_master_db_deadlocks', 'db_deadlocks', labels=['db_name'])
        db_deadlocks.add_metric([get_db['db_name']], get_db['db_deadlocks'])

        replic_status = CounterMetricFamily('pg_master_replic_status', 'replic_status', labels=['db_name'])
        replic_status.add_metric([get_db['db_name']], get_db['replic_status'])
        
        replic_usesysid = CounterMetricFamily('pg_master_replic_usesysid', 'replic_usesysid', labels=['db_name', 'replic_ip'])
        replic_pid = CounterMetricFamily('pg_master_replic_pid', 'replic_pid', labels=['db_name', 'replic_ip'])
        replica_lags = CounterMetricFamily('pg_master_replica_lags', 'replica_lags', labels=['db_name', 'replic_ip'])
        for x in range(get_db['replic_status']):
        	replic_usesysid.add_metric([get_db['db_name'], get_db['replic_ip'][x]], get_db['replic_usesysid'][x])
        	replic_pid.add_metric([get_db['db_name'], get_db['replic_ip'][x]], get_db['replic_pid'][x])
        	replica_lags.add_metric([get_db['db_name'], get_db['replic_ip'][x]], get_db['replica_lags'][x])



        yield size
        yield max_connections
        yield total_connections
        yield left_connections
        yield db_deadlocks
        yield replica_lags
        yield replic_usesysid
        yield replic_pid
        yield replic_status
      

if __name__ == '__main__':

    # Start up the server to expose the metrics.
    start_http_server(server_port)
    # Generate some requests.
    get_db = postgres(host, dbname, user, password)
    REGISTRY.register(CustomCollector())
    while True:
    	time.sleep(1)
    	get_db = postgres(host, dbname, user, password)

    # while True: time.sleep(1)
