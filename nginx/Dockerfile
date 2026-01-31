FROM nginx:alpine

# Install openssl for self-signed cert generation
RUN apk add --no-cache openssl

# Create certs directory
RUN mkdir -p /etc/nginx/certs

# Generate self-signed certificate on build (or entrypoint)
# Validity: 365 days
# CN: localhost (or wildcard)
RUN openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/certs/nginx.key \
    -out /etc/nginx/certs/nginx.crt \
    -subj "/C=KR/ST=Seoul/L=Seoul/O=Dev/OU=Dev/CN=localhost"

# Copy config
COPY default.conf /etc/nginx/conf.d/default.conf
COPY entrypoint.sh /entrypoint.sh

# Install dos2unix to fix Windows line endings
RUN apk add --no-cache dos2unix && \
    dos2unix /entrypoint.sh && \
    chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"]
