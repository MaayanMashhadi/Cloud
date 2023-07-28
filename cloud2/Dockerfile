FROM python:alpine3.17

WORKDIR ./app
COPY server.py .
RUN pip install flask
RUN pip install requests
EXPOSE 8000
ENV FLASK_APP=server.py

ENV FLASK_RUN_PORT=8000
CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0"]