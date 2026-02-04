1. Add it to docker compose:
   ```
   mapproxy-auth-proxy:
    build: ../mapproxy-auth-proxy/
    environment:
      TILE_SERVER_BASE: '' #TODO
      SERVICE_MOUNTPOINT: '/mapproxy_auth_proxy'
      AUTH_REQUIRED: True
      <<: *qwc-service-variables
2. Add the location in the Nginx configuration
   ```
     location ~ ^/(?<t>tenant1|tenant2)/mapproxy_auth_proxy {
        proxy_set_header Tenant $t;
        proxy_set_header Host www.example.com:;
        rewrite ^/[^/]+(.+) $1 break;
        proxy_pass http://mapproxy-auth-proxy:9090;
    }
3. Add the configuration in *config.json*
   ```
   "mapproxy_auth": {
      "source": "https://mapproxy.example.com/mapproxy/",
      "proxy": "https://www.example.com/tenant1/mapproxy_auth_proxy/"
    },
