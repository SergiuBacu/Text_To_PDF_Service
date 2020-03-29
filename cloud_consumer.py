import os, json
from kafka import KafkaConsumer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import google.cloud.storage as gcs
from .models import File

# for details on GCS with Python, see https://github.com/googleapis/python-storage

# set this to the Google Cloud Storage Bucket name
BUCKET_NAME = "sergiu_project2"



def upload_to_gcs(session, user_id, upload_dir, filename):
    """
    upload file to google cloud storage. To set the bucket name, use the constant above
    :param session: db session to use for updating the db's File entry
    :param user_id: user id for the user uploading the file
    :param upload_dir: local directory containing the file to upload
    :param filename: file name to upload
    :return: Success or Failure
    """
    is_success = False

    database_file_query = session.query(File).filter(File.user_id == user_id).filter(File.filename == filename)
    if database_file_query.first().status == "local_converted":
        try:
            # set up GCS bucket connection
            bucket = gcs.Client().get_bucket(BUCKET_NAME)

            # upload blob
            blob = bucket.blob('user/' + str(user_id) + '/pdf/' + filename.replace('txt','pdf'))
            blob.upload_from_filename(filename=os.path.join(upload_dir, filename.replace('txt','pdf')))

            # delete local pdf file
            if os.path.exists(os.path.join(upload_dir, filename.replace('txt', 'pdf'))):
                os.remove(os.path.join(upload_dir, filename.replace('txt', 'pdf')))

            # upload DB with new status
            database_file_query.update({'status':"cloud_google"})
            database_file_query.update({'cloud_url': blob.name})
            session.commit()

            is_success = True
        except Exception as ex:
            print("Exeption in uploading the file to cloud.")
            print(str(ex))

    return is_success

if __name__ == "__main__":
    # set up database session to flask default sqlite database
    engine = create_engine('sqlite:///FirstProject/db.sqlite')
    Session = sessionmaker(bind=engine)
    sonn = engine.connect()
    session = Session(bind=sonn)

    # start comsumer
    print('running consumer...')
    topic_name = 'cloud'
    consumer = KafkaConsumer(topic_name, auto_offset_reset = 'earliest', bootstrap_servers = ['localhost:9092'],
                             api_version = (0,10), consumer_timeout_ms = 1000)
    for msg in consumer:
        file_data = json.loads(msg.value)
        ret = upload_to_gcs(session, file_data['user_id'], file_data['upload_dir'], file_data['filename'])
        if ret:
            print('File {} uploaded successfully to cloud. '.format(file_data['filename'].replace('txt','pdf')))
    consumer.close()
