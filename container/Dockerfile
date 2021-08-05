FROM gallery.ecr.aws/lambda/python:latest
COPY app.py ${LAMBDA_TASK_ROOT}
RUN pip install -r requirements.txt && rm requirements.txt
CMD [ "app.handler" ]
