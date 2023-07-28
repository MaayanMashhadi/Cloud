FROM python:alpine3.17

WORKDIR ./app
COPY diets.py .
RUN pip install Flask
RUN pip install flask_restful
RUN pip install pymongo
ENV FLASK_APP=diets.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=80

CMD ["flask", "run"]