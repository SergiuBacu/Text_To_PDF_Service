import os, json
from time import sleep
from fpdf import FPDF
from .messages import connect_kafka_producer, publish_message
from .models import File
from kafka import KafkaConsumer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# this is a consumer to pull messages from the 'convert' topic, convert the file to pdf, then act as a producer to push
# the file to the 'cloud' topic in order to upload it to the cloud

# RUN THIS IS THE PARENT DIRECTORY OF THE MAIN FLASK PROJECT DIRECTORY AS :
# python -m FirstProject.convert_consumer_producer


def convert_to_pdf(session, user_id, upload_dir, filename):
    """
    convert text file to PDF
    :return: None
    """
    is_success = False

    database_file_query = session.query(File).filter(File.user_id == user_id).filter(File.filename == filename)
    if database_file_query.first().status == "local":
        pdf = FPDF('P', 'in', 'Letter')

        # set the font size
        font_height = 0.16

        # add a page , set margin and enable autyo page break
        pdf.add_page()
        pdf.set_margins(0.25, 0.25)
        pdf.set_auto_page_break(True, margin=0.25)

        # set the font and where the cursor starts
        pdf.set_font('Arial', '', 10)
        pdf.set_xy(0.25, 0.25)

        # open the text filen abd line by line, read from file and write to pdf
        with open(os.path.join(upload_dir, filename), "r") as txt_file:
            line = 1
            while line:
                line = txt_file.readline()
                pdf.write(font_height, line)

        # write out pdf file, use 'latin-1' encoding to avoid unicode issues
        pdf.output(os.path.join(upload_dir, filename.replace('txt', 'pdf'))).encode('latin-1')

        # delete the original file
        if os.path.exists(os.path.join(upload_dir, filename.replace('txt', 'pdf'))):
            os.remove(os.path.join(upload_dir, filename))

        # upload DB with new status
        database_file_query.update({'status':"local_converted"})
        session.commit()

        is_success = True

    return is_success

if __name__ == "__main__":
    # set up database session to flask default sqlite database
    engine = create_engine('sqlite:///FirstProject/db.sqlite')
    Session = sessionmaker(bind=engine)
    sonn = engine.connect()
    session = Session(bind=sonn)

    # start comsumer
    print('running consumer...')
    file_converted = []
    topic_name = 'convert'
    processed_topic_name = 'cloud'
    consumer = KafkaConsumer(topic_name, auto_offset_reset = 'earliest', bootstrap_servers = ['localhost:9092'],
                             api_version = (0,10), consumer_timeout_ms = 1000)
    for msg in consumer:
        file_data = json.loads(msg.value)
        ret = convert_to_pdf(session, file_data['user_id'], file_data['upload_dir'], file_data['filename'])
        if ret:
            file_converted.append(file_data)
    consumer.close()
    sleep(5)

    # publish message to "cloud" topic  to upload converted pdf files to the cloud
    if len(file_converted) > 0:
        print('publishing messages...')
        producer = connect_kafka_producer()
        for data in file_converted:
            publish_message(producer, processed_topic_name, 'cloud', json.dumps(data))
