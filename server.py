"""
Copyright © 2025 by BGEO. All rights reserved.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from flask import Flask, request, Response, stream_with_context
from flask_jwt_extended import jwt_required
from qwc_services_core.auth import auth_manager
from qwc_services_core.tenant_handler import TenantHandler
import requests
from requests.adapters import HTTPAdapter
# from requests.packages.urllib3.util.retry import Retry
import os
import logging
import ssl
from urllib.parse import urlparse

# Initialize Flask app
app = Flask(__name__)
app.logger.setLevel(logging.INFO)

# Initialize tenant handler
tenant_handler = TenantHandler(app.logger)

# Initialize JWT manager
jwt = auth_manager(app)

# Configure tile server base URL (from environment)
TILE_SERVER_BASE = os.getenv('TILE_SERVER_BASE', 'https://tile-server:443')

# Create reusable session with HTTPS support
session = requests.Session()

# Configure adapter with SSL context
adapter = HTTPAdapter(
    pool_connections=100,
    pool_maxsize=100,
)
session.mount('https://', adapter)

@app.route('/<path:path>', methods=['GET'])
@jwt_required()
def tile_proxy(path):
    """Proxy tile requests with JWT authentication and HTTPS forwarding"""
    try:
        # Get tenant information
        tenant = tenant_handler.tenant()
        app.logger.debug(f"Processing tile request for tenant: {tenant}")

        # Construct target URL with HTTPS
        query_string = request.query_string.decode('utf-8')
        target_url = f"{TILE_SERVER_BASE}/{path}?{query_string}" if query_string else f"{TILE_SERVER_BASE}/{path}"

        # Prepare headers (remove Host to avoid conflicts)
        headers = {k: v for k, v in request.headers if k.lower() not in ['authorization']}
        headers['X-Forwarded-For'] = request.remote_addr

        # Log request for debugging (consider reducing in production)
        app.logger.debug(f"Forwarding to: {target_url}")

        # Forward request to tile server with streaming
        resp = session.get(
            target_url,
            headers=headers,
            cookies=request.cookies,
            stream=True,
            timeout=(2.0, 15.0)  # Connect timeout, read timeout
        )

        # Handle tile server errors
        if resp.status_code != 200:
            app.logger.error(f"Tile server error: {resp.status_code} for {target_url}")
            return Response(
                f"Tile server error: {resp.status_code}",
                status=resp.status_code,
                content_type=resp.headers.get('Content-Type', 'text/plain')
            )

        # Stream response back to client
        return Response(
            stream_with_context(resp.iter_content(chunk_size=16384)),  # Larger chunks for tiles
            content_type=resp.headers.get('Content-Type', 'image/png'),
            headers={
                'Cache-Control': 'public, max-age=31536000',  # 1 year cache
                'X-Tenant': tenant,
                'X-Tile-Source': urlparse(TILE_SERVER_BASE).hostname
            }
        )

    except requests.exceptions.SSLError as e:
        app.logger.error(f"SSL error: {str(e)}")
        return {'error': 'Secure connection failed'}, 502
    except requests.exceptions.Timeout:
        app.logger.error("Tile server timeout")
        return {'error': 'Tile server timeout'}, 504
    except requests.exceptions.ConnectionError as e:
        app.logger.error(e)
        app.logger.error("Cannot connect to tile server")
        return {'error': 'Cannot connect to tile server'}, 502
    except Exception as e:
        app.logger.exception(f"Proxy error: {str(e)}")
        return {'error': 'Internal server error'}, 500


""" liveness probe endpoint """
@app.route("/healthz", methods=['GET'])
def healthz():
    return {"status": "OK"}


