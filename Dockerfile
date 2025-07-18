FROM python:3.13-alpine3.22
ARG BUILD_DATE
LABEL org.label-schema.build-date=$BUILD_DATE
LABEL maintainer="rapid-prototyping@agh.edu.pl"
LABEL org.label-schema.schema-version="1.0"
LABEL org.label-schema.docker.cmd=""
WORKDIR app
COPY *.py .
COPY requirements.txt .
RUN python3 -m pip install -r requirements.txt --break-system-packages
RUN echo -e "0 5 * * *\t/app/main.py -o cpv" | crontab -
CMD ["sh", "-c", "python3 main.py -o cpv && crond -f"]
