FROM python:alpine3.17

WORKDIR ./app
COPY meals.py .
RUN pip install Flask
RUN pip install pymongo
RUN pip install requests
ENV FLASK_APP=meals.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=80

CMD ["flask", "run"]