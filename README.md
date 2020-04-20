# Text to PDF Service


## **Table of Contents**

**1. About Project**

**2. Technologies and Tools**

**3. User Access**

**4. Uploading Documents**

**5. Downloading Documents**

------------------------------------------------------------------------------------------

### 1. About Project 

 * _Cloud Computing_ 
  
Cloud computing technology is  the availability of computing resources over the internet.
Because of this technology, users no longer had to rely on data transmission devices like local hard drives, and thus a rapid progress of development was made possible.
A diagram of how the cloud technology works can be seen below.
![Cloud Computing Diagram](https://github.com/SergiuBacu/Text_To_PDF_Service/blob/master/resources/Cloud_computing.svg)(From Wikipedia)

Cloud Technology can only be accessed over the internet. There are different types of cloud technologies. A private cloud is one where a private network hosts cloud-like resources, but they are not available for public consumption. A public cloud is where computing resources are available publicly over the internet. A hybrid cloud is a combination of these two approaches.

  * _Cloud Computing Application_

The project uses Google Cloud Storage to save and access the converted files, without the use of the local disk space.
The tracking of data is made possible through a database that records all the saved files, and use it to solve the problem of data duplication.
The service is available only from within a profile, therefore, in order for a user to use the service, the user has to create an account, and then authenticate with the created credentials. Basic HTTP authentication and session cookies are used.
The project was developed in Python 3.8.2 and uses the Flask framework to manage the functionalities of SignUp, SignIn, LogIn, LogOut.
The project  also uses Apache Kafka for asynchronous processing of the pdf files.

### 2. Technologies and Tools

The project's overview can be seen in the diagram below. 
![Project Diagram](https://github.com/SergiuBacu/Text_To_PDF_Service/blob/master/resources/Project_Diagram.jpg)

 * ### _Apache Kafka_	

With the spread of event based architectures, messaging systems have become the basic components of enterprise architectures. Because  enterprise applications process more and more data, the performance of messaging systems and the need for rapid and scalable platforms have become paramount in importance for the smooth running of the applications.
 Apache Kafka is one of the most efficient messaging systems that can transfer up to 1 million messages per second in a group of three computers of average performance.
In Kafka there is a producer of messages and a consumer of those messages. The producer publishes messages in Kafka, that become available to cosumers for processing, but the consumers don’t have to confirm the processing. Kafka stores all the messages received in a fixed period of time, and the cosumers have the liberty to consume any of the stored messages. Because of this, Kafka has a series of advantages:
1)  It simplifies the architecture of the system
2)  Kafka doesn’t have to keep a record of which messages were consumed and which were not. It isolates the producers from the consumers. In the systems in which the consumers are obligated to confirm the processing of messages, the systems’s performance can decrease once the number of messages rises. Some services limit the rate at which the producers can publish messages, to prevent the overloading of the messaging system. Unfortunately this can lead to dangerous situations where a slow but unimportant consumer affects a producer which is critical for business.
3) The consumers don’t have to constantly consume. Thus the consumers can be stopped anytime without affecting the messaging system. They can even be batch jobs periodically executed. But this approach works only if the messages are stored in Kafka long enough for the processes to process the data between sessions.
4) Because the messages don’t have to be selected when stored, Kafka can use a storage model called “messaging journal”. This journal is a messaging queue in which the new messages are always added at the end of the list. The existing messages never change. Because the journal is modified only at the end by adding new messages, it can be optimally stored on magnetic storage devices – the writes on the hard-disk can be done sequentially, thus avoiding a decrease in performance. If the consumers manage to keep up with the producers, Kafka can deliver messages directly from memory, using a caching mechanism offered by the operating system.

Another important difference from traditional systems is the way messages can be consumed.
Traditional systems offer 2 ways of consuming:
1. Queue
2. Publish-Subscribe

In the “queue” model, each message reaches a single consumer. In the “Publish-Subscribe” model, each message reaches each consumer. Kafka implements a single abstraction that covers both models, called the “consumers group”. In Kafka, every consumer is part of a group, even if the consumer is alone in the group. Within a group, only one consumer can receive messages. But messages are delivered to all groups of consumers. This approach allows the system to offer a single way to group the messages : using topics. Kafka is a “publish-subscribe” model, in which subscription is done by groups of consumers, and not by consumers alone. If all the consumers are part of the same group, every message  will reach only one consumer from a group, the topic acting like a queue. But if each consumer is part of a different group, then all the consumers will receive the published messages – the classic public-subscribe model. In reality though, we will have to deal with a small number of groups of consumers, each group corresponding to a service that is interested in the data published by Kafka. Within the groups, we will have many consumers (usually one for each computer that runs the service). Because each group receives each message published in a topic, the services will receive all the published messages, but within a service the message processing will be distributed between computers.
![Kafka](https://github.com/SergiuBacu/Text_To_PDF_Service/blob/master/resources/Kafka_Messaging_Pic.jpg)

* #### Kafka Architecture

Broadly, a Kafka service is formed from many computers that have the role of a broker, recording the published messages. Besides that, there is the need of a group of computers to run Zookeeper. Kafka uses Zookeeper to coordinate and manage the brokers.
The quantity of messages published on one topic can exceed the capacity of a broker, therefore the topics are divided in “partitions”.  Each partition is in fact a “message journal”. The partitions need to fit entirely on a broker and the partitions that belong to one topic are uniformly distributed between brokers, each broker having almost the same number of partitions.
![KafkaProducerConsumer](https://github.com/SergiuBacu/Text_To_PDF_Service/blob/master/resources/Kafka_Producer_Consumer.jpg)

When a producer wants to publish a message in Kafka, he interogates a broker to find out how many partitions there are, and how the partitions are distributed among the brokers. The producer decides what partition to use (based on the content of the message, random or looping through the patitions), then the producer sends the message to the broker that hosts the chosen partition.
On the consumers side, the partitions of a topic are equaly distributed between the consumers of a group, every consumer receiving one or more partitions which he can read messages from. Besides the uniform distribution of tasks to consume messages, the partition distribution guarantees that each message will be processed by a single consumer from a group.
The index of the last processed message of every partition is recorded in Zookeeper, therefore if a consumer leaves the group, that consumer’s partitions can be reasigned to other consumers, which can resume the process from the last message that was read. When a broker leaves the group, or becomes inaccessible, his partitions can become inaccessible or lost. To prevent these kind of situations,  Kafka has introduced the idea of “replicated partitions”. Each partition that is hosted by a broker can have one or more replica. The replicas are partitions as well, but these partitions are hosted by different brokers than the original. Producers cannot publish messages in replicas, only in the original (called leading partitions), and the brokers that host the original partition make sure that every received message is saved in replicas as well. In the event a broker is lost, one of the replicas of every original partition of that broker takes the lead as the original partition. And thus, Kafka manages to work without interruptions and without loss of data. When the broker is resuming his activity, he syncronizes his partitions from the other brokers, and after that begins a process of assigning of leaders for each partition.

* #### ZooKeeper

Kafka uses Zookeeper to detect crashes, to implement the discovery of topics, and to maintain the production and the consumption state for topics. The design of Zookeeeper is specialized and very focused on coordination tasks.
ZooKeeper enables coordination tasks for distributed systems. A distributed system is a system with multiple components, which are located on different machines that communicate with each other and coordinate actions between them, so that they appear as a single coherent system. A coordination task is a task that involves multiple processes.
These tasks can be for the purpose of cooperation or for the purpose of regulating contention. When we talk about cooperation, it means that processes need to work together and take action to enable other processes to make progress. To understand cooperation better, we can look at a simple master-worker architecture. In this type of archtecture, the worker informs the master that it is available for assignments. The master then assigns tasks to the worker.
Contention, on the other hand, means that two processes have to run one after the other because they cannot make progress concurrently. Using the master-worker example, we want to have a single master, but because multiple processes may try to become the master, these processes need to implement mutual exclusion. The task of acquiring mastership can be likened to the task of acquiring a lock, which means the process that acquired the master lock exercises the role of master. Similar problems can be found in multithreaded programs.  ZooKeeper implements synchronization primitives and also provides a shared store with some special ordering properties.

More information on ZooKeeper can be found at this link https://www.oreilly.com/library/view/zookeeper/9781449361297/ch01.html

* #### Flask

Flask is a Web Server Gateway Interface that describes the way a server communicates with web applications and how these applications can be chained for processing one request. Flask is different from other frameworks because it gives full creative control over the applications. It comes with a robust core that include all the  basic functionalities, and the rest can be added by third-party extensions, thus Flask can have a variety of applications. Flask doesn’t have native support for accessing databases, so in order to use this feature we need to access the Flask extensions.

The project uses Flask to render templates and  to manage and secure login and logout events, as well as import blueprints.

For more information about flask, see the O’REILLY book “Flask Web Development ” - Miguel Grinberg

* ##### Flask-Login

Flask-Login is a small extension that specilizes in managing the user authentication system, without being tied to a specific authentication mechanism.

Flask-Login provides user session management for Flask. It handles the common tasks of logging in, logging out, and remembering the user’s session over extended periods of time.

Flask-Login properties:

1) It stores the active user’s ID in the session and lets you log them in and out easily.

2) It lets you restrict views to logged-in (or logged-out) users.

3) It handles the normally-tricky “remember me” functionality.

4) It helps protect your user’s sesions from being stolen by cookie thieves.

* #### SQLAlchemy

SQLAlchemy has two major modes of usage, SQL Expression Language (referred to as Core), and ORM. The modes can be used separately or together, depending on the application. Its major components are illustrated below, with component dependencies organized into layers:
![Image description](link-to-image)

In the figure above, the two most significant front-facing portions of SQLAlchemy are the Object Relational Mapper, and the SQL Expression Language. SQL Expressions can be used independently of the ORM. When using the ORM, the SQL Expression language remains part of the public facing API as it is used within object-relational configurations and queries.
The two modes use slightly different syntax, but the biggest difference between the two is the view of data as schema or business objects. SQLAlchemy Core has a schema-centric view, which follows the traditional SQL model, being focused around tables, keys and index structures. SQLAlchemy Core’s strongest points are Data Warehouse, Reporting, Analysis, and where operating on unmodeled data and control of the query is useful.


For more information on SQLAlchemy see “Essential SQLAlchemy ” by Jason Myers and Rick Copeland

* #### Setup

In order for the user to be able to run the application, the user must first setup the environment.
The system must have Kafka and Zookeeper installed.
Setup Kafka according to Kafka's documentation.
FlaskFirst.conf, FlaskFirst.py, and FlaskFirst.wsgi have been provided as example config files.
Then we must set the environmental variables for the User and for the System.
Some of the variables are already set when we install PyCharm, Flask and Zookeeper, and others we have to introduce.

Below is a list of environmental variables we must have for the project to run.

* ##### For the User
	1. FLASK_APP=MyProject (where “MyProject” is the name of the python project)
	2. FLASK_DEBUG=1
	3. ZOOKEEPER_HOME=...\apache-zookeeper-X.Y.0-bin (the variable must be set to the directory where Zookeeper is installed)
	4. GOOGLE_APPLICATION_CREDENTIALS=...\<ProjectFolder>\Filename.json (The JSON file from the project’s directory)

* ##### For the System
	1. PATH=”…\Oracle\Java\javapath%”

We must have Zookeeper and Kafka server running. For that we must execute the scripts that start the services, from the respective \bin\ directories.

The user can start and stop and verify the status of Kafka and Zookeeper with the commands below:  
1) *zkServer.cmd start* (Windows) or *./zkServer.sh start* (Linux)
2) *zkServer.cmd stop* (Windows) or *./zkServer.sh stop* (Linux)
3) *zkServer.cmd status* (Windows) or *systemctl status zookeeper* (Linux)
4) *kafka-server-start* .../config/server.properties (Windows) or *./kafka-server-start.sh* .../config/server.properties (Linux)  
5) *kafka-server-stop* (Windows) or *./kafka-server-stop.sh* (Linux)


### 3. User Access


In order to access the Flask Application, the user must have access to the server (e.g. http://127.0.0.1:5000).
The application is run from the CLI using the command “flask run” which is supposed to run in parent directory of the project.
Once the server is accessed the user will be directed to the Home page of the Flask application.
The sections of the page are Home, Sign Up, and Login, which are templates rendered by the flask application.
The project also uses a CSS file for the page layout.

* ##### Home

This is the page that is loaded first when the user accesses the server
![Home Page](https://github.com/SergiuBacu/Text_To_PDF_Service/blob/master/resources/Home.jpg)

* ##### Sign Up

In order to create an account, the user must provide an email address, a name, and a password. The email, the name, and the password provided are then stored into the database for future login attempts. The password is securely hashed when stored in the database.
When a user provides an email address, the flask application will compare the address with the records from the database, and if the email is in the database, it means the address was used for another account and the flask application will return an error.

![Sign Up](https://github.com/SergiuBacu/Text_To_PDF_Service/blob/master/resources/SignUp.jpg)

When the error message is displayed the page will look like the below.

![Sign Up Error](https://github.com/SergiuBacu/Text_To_PDF_Service/blob/master/resources/SignUp_Error.jpg)

The Login page should appear as the image below.

![Login Page](https://github.com/SergiuBacu/Text_To_PDF_Service/blob/master/resources/Login.jpg)

When the user provides valid credentials, the flask application will grant access and the user will be redirected to the Profile page. The profile page will contain a “Welcome” message followed by the name from the database which the user has provided at sign up.

The “Login” button will then be replaced with a “Log Out” button and thus the user’s session will be secured, as two users cannot use the same session without creating conflict.

The Profile page should look like the page shown below.

![Profile](https://github.com/SergiuBacu/Text_To_PDF_Service/blob/master/resources/Profile.jpg)

### 4. Uploading Documents

After the user has successfully signed in, The “Welcome” page will contain two links, one for uploading files, and one for downloading the uploaded files.

In order to upload a file successfully, the file must contain a name different from all the filenames in the database, otherwise the uploading will fail with the message “The file exists, please try again.”

After the file is uploaded, the application will convert the file to pdf.

The uploading page looks like the image below.

![Uploading Page](https://github.com/SergiuBacu/Text_To_PDF_Service/blob/master/resources/Upload.jpg)

If the uploaded was successfully the page should look like the one below.

![Uploading_Successfully](https://github.com/SergiuBacu/Text_To_PDF_Service/blob/master/resources/UploadedSuccessfuly.jpg)

### 5. Downloading Documents

After the user has successfully uploaded the document, the application will convert the file into PDF format and allow the user to download the converted file. Also the user will be able to download files from previous uploads.

![Downloading Page](https://github.com/SergiuBacu/Text_To_PDF_Service/blob/master/resources/DownloadFile.jpg)

### 6. Converting Text to PDF

The kafka consumer to convert the text file to PDF can be run manually or scheduled as a task. To run it, the user must be in the parent directory of the project, the same level at which 'flask run' is executed. It should be run as a module using the command "python -m FlaskProject.convert_consumer_producer".
This is also a producer for uploading to cloud storage. 
![ConsumerConversion](https://github.com/SergiuBacu/Text_To_PDF_Service/blob/master/resources/ConsumerConversion.jpg)

### 7. Upload PDF to Cloud

There is a second kafka consumer that uploads converted PDF file to the cloud. It can be run manually or scheduled as a task.
To run it, the user must be in the parent directory of the project, the same level at which 'flask run' is executed. It should be run as a module using the command "python -m FlaskProject.cloud_consumer".
![CloudUpload](https://github.com/SergiuBacu/Text_To_PDF_Service/blob/master/resources/CloudUpload.jpg)


