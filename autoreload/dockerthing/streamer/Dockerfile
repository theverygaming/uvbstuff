FROM alpine:3.19
RUN apk add --no-cache ffmpeg #py3-pip
#RUN pip3 install --break-system-packages ""
WORKDIR /app
COPY . .
RUN adduser --disabled-password --uid 101 --home /app user
USER user
WORKDIR /app
CMD ["./entry.sh"]
