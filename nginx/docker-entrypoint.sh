#!/bin/sh
set -e

CERT_DIR=/etc/nginx/certs
KEY="$CERT_DIR/fitnesstracker.local.key"
CRT="$CERT_DIR/fitnesstracker.local.crt"

if [ ! -f "$KEY" ] || [ ! -f "$CRT" ]; then
    mkdir -p "$CERT_DIR"

    # Write a full openssl config with SAN so modern browsers trust the cert
    cat > /tmp/openssl.cnf <<EOF
[req]
distinguished_name = req_distinguished_name
x509_extensions    = v3_req
prompt             = no

[req_distinguished_name]
C  = US
ST = Dev
L  = Local
O  = FitTrack
CN = fitnesstracker.local

[v3_req]
subjectAltName = DNS:fitnesstracker.local, DNS:localhost
EOF

    openssl req -x509 -nodes -newkey rsa:2048 \
        -keyout "$KEY" \
        -out    "$CRT" \
        -days   3650 \
        -config /tmp/openssl.cnf

    rm /tmp/openssl.cnf
    echo "[nginx] Self-signed certificate generated for fitnesstracker.local"
fi

exec nginx -g "daemon off;"
