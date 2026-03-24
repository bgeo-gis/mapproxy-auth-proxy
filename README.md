1. Add it to docker compose:
   ```
   mapproxy-auth-proxy:
    build: ../mapproxy-auth-proxy/
    environment:
      TILE_SERVER_BASE: '' #TODO
      AUTH_REQUIRED: True
      <<: *qwc-service-variables
   ```
2. Add the location in the Nginx configuration
   ```
   location ~ ^/(?<t>tenant1|tenant2)/mapproxy_auth_proxy {
       proxy_set_header Tenant $t;
       rewrite ^/[^/]+/mapproxy_auth_proxy/?(.*)$ /$1 break;
       proxy_pass http://mapproxy-go-auth-proxy:9090;

       # optional but nice: preserve real client IP chain
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       proxy_set_header X-Forwarded-Proto $scheme;
   }
   ```
3. Add the configuration in *config.json*
   ```json
   "mapproxy_auth": {
      "source": "https://mapproxy.example.com/mapproxy/",
      "proxy": "https://www.example.com/tenant1/mapproxy_auth_proxy/"
    },
   ```


Environment

- Required:
  - TILE_SERVER_BASE: Upstream tile server base URL (http(s)://host[:port][/basepath])
  - JWT_SECRET_KEY: HS256 secret for verifying JWTs
- Optional:
  - PORT: Listen port (default: 9090)
  - AUTH_REQUIRED: true/false (default: true)
  - JWT_ACCESS_COOKIE_NAME: cookie name to read JWT from (default: access_token_cookie)
  - CONNECT_TIMEOUT: e.g. 2s (default: 2s)
  - RESPONSE_HEADER_TIMEOUT: e.g. 15s (default: 15s)
