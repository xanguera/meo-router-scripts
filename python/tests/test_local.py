"""Tests with a local fake HTTP gateway: never contacts a real device."""
import base64
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import pathlib
import sys
import threading
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import meo_gr241ag as app


class Handler(BaseHTTPRequestHandler):
    submitted = []

    def log_message(self, *_):
        pass

    def do_GET(self):
        expected = "Basic " + base64.b64encode(b"meo:secret").decode()
        if self.path != "/index.html" or self.headers.get("Authorization") != expected:
            self.send_error(401)
            return
        self.send_response(200)
        self.send_header("Set-Cookie", "SESSIONID=testing-session; Path=/")
        self.end_headers()
        self.wfile.write(b"ok")

    def do_PUT(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode()
        if "SESSIONID=testing-session" not in self.headers.get("Cookie", ""):
            self.send_error(403)
            return
        Handler.submitted.append((self.path, body, self.headers.get("Content-Type", "")))
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'{"ok":true}')


class ScriptsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)

    def setUp(self):
        Handler.submitted = []

    def test_http_wifi_mesh_wps(self):
        # Inject local mock port by replacing the login URL only for tests.
        real_login = app.http_login
        port = self.server.server_port

        def mock_login(host, username, password):
            import http.cookiejar, urllib.request
            jar = http.cookiejar.CookieJar()
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPCookieProcessor(jar))
            root = f"http://127.0.0.1:{port}"
            authorization = base64.b64encode(f"{username}:{password}".encode()).decode()
            request = urllib.request.Request(root + "/index.html", headers={"Authorization": "Basic " + authorization})
            app.http_request(opener, request)
            self.assertTrue(any(cookie.name == "SESSIONID" for cookie in jar))
            return opener, root

        with patch.object(app, "http_login", side_effect=mock_login):
            for feature, action in [("wifi", "off"), ("mesh", "off"), ("wps", "off")]:
                self.assertEqual(app.http_modify("127.0.0.1", "meo", "secret", feature, action), 0)
        self.assertEqual(len(Handler.submitted), 3)
        self.assertEqual(Handler.submitted[0][0], "/locallmngt.cmd?request=/generic-wifi")
        self.assertIn('"enableWifi":"0"', Handler.submitted[0][1])
        self.assertEqual(Handler.submitted[1][0], "/locallmngt.cmd?request=/settings")
        self.assertIn('"smartMesh":"0"', Handler.submitted[1][1])
        self.assertIn('"wps":false', Handler.submitted[2][1])
        self.assertIn('"wpsOptions":3', Handler.submitted[2][1])
        self.assertIn("charset=UTF-8", Handler.submitted[0][2])

    def test_dry_run_has_no_connection(self):
        with patch.object(app, "http_login") as login, patch.object(app, "telnet_commands") as telnet:
            self.assertEqual(app.main(["mesh", "off"]), 0)
            login.assert_not_called()
            telnet.assert_not_called()

    def test_invalid_private_host(self):
        self.assertEqual(app.valid_host("192.168.1.254"), "192.168.1.254")
        with self.assertRaises(Exception):
            app.valid_host("8.8.8.8")

    def test_mesh_status_not_implemented(self):
        self.assertEqual(app.main(["mesh", "status"]), 2)

    def test_prompts_use_defaults_and_no_confirmation(self):
        with patch("builtins.input", side_effect=["", ""]) as ask, \
             patch("getpass.getpass", return_value="secret"), \
             patch.object(app, "http_modify", return_value=0) as modify:
            self.assertEqual(app.main(["wifi", "off", "--apply"]), 0)
            self.assertEqual(ask.call_count, 2)
            modify.assert_called_once_with("192.168.1.254", "meo", "secret", "wifi", "off")

    def test_user_can_override_ip_username_interactively(self):
        with patch("builtins.input", side_effect=["192.168.1.100", "admin"]), \
             patch("getpass.getpass", return_value="secret"), \
             patch.object(app, "http_modify", return_value=0) as modify:
            self.assertEqual(app.main(["mesh", "off", "--apply"]), 0)
            modify.assert_called_once_with("192.168.1.100", "admin", "secret", "mesh", "off")

    def test_flags_skip_interactive_ip_and_user(self):
        with patch("builtins.input") as ask, \
             patch("getpass.getpass", return_value="secret"), \
             patch.object(app, "http_modify", return_value=0) as modify:
            self.assertEqual(app.main(["wifi", "on", "--apply", "--host", "10.0.0.1", "--user", "admin"]), 0)
            ask.assert_not_called()
            modify.assert_called_once_with("10.0.0.1", "admin", "secret", "wifi", "on")

    def test_reject_unsafe_username(self):
        with self.assertRaises(Exception):
            app.valid_username("meo\r\n/lan/bridge-mode/config")
        with self.assertRaises(Exception):
            app.valid_username("meo:wrong")

    def test_wifi_telnets_use_known_index(self):
        from unittest.mock import AsyncMock
        with patch("builtins.input", side_effect=["", ""]), patch("getpass.getpass", return_value="secret"), patch.object(app, "telnet_commands", new_callable=AsyncMock) as run:
            self.assertEqual(app.main(["wifi", "status"]), 0)
            commands = run.call_args.args[-1]
            self.assertEqual(commands, ["/wireless/basic/show --wifi-index=0", "/wireless/basic/show --wifi-index=1"])


if __name__ == "__main__":
    unittest.main()
