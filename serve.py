"""Serve this site locally.
"""
import http.server
import os

from milc import cli


@cli.argument('-H', '--host', arg_only=True, default='127.0.0.1', help='IP to listen on.')
@cli.argument('-p', '--port', arg_only=True, default=8937, type=int, help='Port number to use.')
@cli.entrypoint('Run a local webserver.')
def docs(cli):
    """Spin up a local HTTPServer instance.
    """
    with http.server.HTTPServer((cli.args.host, cli.args.port), http.server.SimpleHTTPRequestHandler) as httpd:
        cli.log.info("Serving QMK docs at http://%s:%d/", cli.args.host, cli.args.port)
        cli.log.info("Press Control+C to exit.")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            cli.log.info("Stopping HTTP server...")
        finally:
            httpd.shutdown()


if __name__ == '__main__':
    cli()
