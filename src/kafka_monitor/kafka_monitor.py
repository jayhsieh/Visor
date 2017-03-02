from pyspark import SparkContext, SparkConf
from pyspark.streaming import StreamingContext
from pyspark.streaming.kafka import KafkaUtils
import json
import os
import smtplib
import time
import datetime


class kafka_monitor(object):

	def __init__(self, config, config_private):
		# Load config file
		self.config = config
		# Load private config file
		self.config_private = config_private
		# Define Spark configuration
		conf = SparkConf()
		conf.setMaster(self.config['master_url'])
		conf.setAppName(self.config['app_name'])
		# Initialize a SparkContext
		sc = SparkContext(conf=conf)
		# Set the batch interval to be 1 sec
		self.ssc = StreamingContext(sc, self.config['batch_interval'])

		# Set the Kafka related params
		self.addr = self.config['kafka']['addr']
		self.topic = self.config['kafka']['topic']	

		# Set the summary report params
		# report interval: in terms of sec
		self.report_inetrval = self.config['email']['report']['inetrval']
		self.error_cnt = 0
		self.error_li = []

	
	# Send an email every time detects an error log
	def error_alert_email(self, error):
		# In case of empty list
		# Check if the report system is on
		if len(error) > 0 and self.config['email']['alert']['on']:
			# Parse the error	
			error_li = error[0].split(']')
			error_time = error_li[0].lstrip('[')
			error_client = error_li[3].split(' ')[2]
			error_msg = error_li[4].rstrip('\n')	

			TO = self.config['email']['alert']['receiver']
			SUBJECT = self.config['email']['alert']['subject']
			TEXT = '''
An error occurred in the cluster.

time: %s

client: %s

message: %s
		''' % (error_time, error_client, error_msg) 
	
			# Sender Gmail Sign In
			gmail_sender = self.config_private['email']['address']
			gmail_passwd = self.config_private['email']['password']

			server = smtplib.SMTP('smtp.gmail.com', 587)
			server.ehlo()
			server.starttls()
			server.login(gmail_sender, gmail_passwd)

			BODY = '\r\n'.join(['To: %s' % TO,'From: %s' % gmail_sender,'Subject: %s' % SUBJECT,'', TEXT])

			try:	
				server.sendmail(gmail_sender, [TO], BODY)
				print ('email sent')
			except:
				print ('error sending mail')

			server.quit()

	
	
	# Send an email every pre-defined time (30 min / 2 hrs / 1 day ...)
	# to report the summary
	def summary_report_email(self, errors, error_cnt):
		if self.config['email']['report']['on']:
			TO = self.config['email']['report']['receiver']
			SUBJECT = self.config['email']['report']['subject']
			TEXT = '''
Error count: %d

Errors:
			''' % (error_cnt)

			if len(errors) == 0:
				TEXT += 'None'
			else:
				for error in errors:
					TEXT += error

			# Sender Gmail Sign In
			gmail_sender = self.config_private['email']['address']
			gmail_passwd = self.config_private['email']['password']

			server = smtplib.SMTP('smtp.gmail.com', 587)
			server.ehlo()
			server.starttls()
			server.login(gmail_sender, gmail_passwd)

			BODY = '\r\n'.join(['To: %s' % TO,'From: %s' % gmail_sender,'Subject: %s' % SUBJECT,'', TEXT])

			try:
				server.sendmail(gmail_sender, [TO], BODY)
				print ('email sent')
			except:
				print ('error sending mail')

			server.quit()



	def run(self):
		# Consume Kafka streams directly, without receivers
		lines = KafkaUtils.createDirectStream(self.ssc, [self.topic], {"metadata.broker.list": self.addr}).window(30, 30)
		#lines.foreachRDD(lambda x: print(x.collect()))
		val_lines = lines.map(lambda x: x[1])
		#val_lines.foreachRDD(lambda x: print(x.collect()))
		#useful_lines = val_lines.filter(lambda x: 'HEARTBEAT' not in x)

		error_lines = val_lines.filter(lambda x: 'ERROR' in x)

		#error_lines.foreachRDD(lambda x: print(x.collect()))
		error_lines.foreachRDD(lambda x: self.error_alert_email(x.collect()))

		# Generate summary report every window time
		error_sum_lines = error_lines.window(self.report_inetrval, self.report_inetrval)
		error_sum_lines.foreachRDD(lambda x: self.summary_report_email(x.collect(), x.count()))

		#####################################################
		# Start the streaming process
		self.ssc.start()

		'''counter = 0
		while counter <= self.report_inetrval:
			if counter == self.report_inetrval:
				self.summary_report_email()
				self.error_cnt = 0
				self.error_li = []
				#print('>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<')
				counter = 0
			else:
				# Sleep 1 sec
				time.sleep(1)
				# Increase the counter
				counter += 1
		'''

		self.ssc.awaitTermination()

if __name__=="__main__":
	# Load the configurations
	with open(os.environ['VISORHOME']+"/config/kafka_monitor.json") as config_file:
		config = json.load(config_file)

	# Load private email information
	with open(os.environ['VISORHOME']+"/config/private.json") as private_file:
		config_private = json.load(private_file)

	monitor = kafka_monitor(config, config_private)
	monitor.run()

