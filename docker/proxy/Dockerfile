FROM nginx:1.20-alpine
RUN mkdir -p /opt/primming/static && \
    mkdir -p /var/www/wordpress && \
    mkdir -p /var/www/certbot/.well-known

COPY primming.conf /etc/nginx/conf.d/default.conf