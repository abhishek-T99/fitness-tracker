FROM nginx:alpine

# openssl is needed to generate the self-signed certificate at first boot
RUN apk add --no-cache openssl

# Remove the default site config shipped with the image
RUN rm -f /etc/nginx/conf.d/default.conf

COPY fittrack.conf       /etc/nginx/conf.d/fittrack.conf
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN  chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
