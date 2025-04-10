import socket
import threading


def relay(source, destination):
    try:
        while True:
            data = source.recv(4096)
            if not data:
                break
            destination.sendall(data)
    except Exception:
        pass
    finally:
        try:
            source.shutdown(socket.SHUT_RD)
        except Exception:
            pass
        try:
            destination.shutdown(socket.SHUT_WR)
        except Exception:
            pass


def handle_client(client_socket):
    try:
        request = client_socket.recv(4096)
        if not request:
            client_socket.close()
            return

        # Check if the method is CONNECT (for HTTPS tunneling)
        if request.startswith(b'CONNECT'):
            # Parse the CONNECT request to extract host and port
            first_line = request.split(b'\n')[0]
            try:
                _, target, _ = first_line.split(b' ')
                target_host, target_port = target.split(b':')
                target_host = target_host.decode('utf-8')
                target_port = int(target_port.decode('utf-8'))
            except Exception:
                client_socket.close()
                return

            # Connect to the target server
            try:
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_socket.connect((target_host, target_port))
            except Exception:
                client_socket.send(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
                client_socket.close()
                return

            # Send a 200 Connection Established response back to the client
            client_socket.send(b"HTTP/1.1 200 Connection Established\r\n\r\n")

            # Start bidirectional relay between client and server
            thread1 = threading.Thread(target=relay, args=(client_socket, server_socket))
            thread2 = threading.Thread(target=relay, args=(server_socket, client_socket))
            thread1.start()
            thread2.start()
            thread1.join()
            thread2.join()
        else:
            # For regular HTTP requests, parse the request to get the host and port
            first_line = request.split(b'\n')[0]
            try:
                method, url, protocol = first_line.split(b' ')
            except Exception:
                client_socket.close()
                return

            # Extract host:port from the URL
            http_pos = url.find(b'://')
            if http_pos != -1:
                url = url[http_pos + 3:]
            port = 80
            webserver_pos = url.find(b'/')
            if webserver_pos == -1:
                webserver_pos = len(url)
            port_pos = url.find(b':')
            if port_pos != -1 and port_pos < webserver_pos:
                try:
                    port = int(url[port_pos + 1:webserver_pos])
                except ValueError:
                    port = 80
                webserver = url[:port_pos]
            else:
                webserver = url[:webserver_pos]

            try:
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_socket.connect((webserver.decode('utf-8'), port))
                server_socket.sendall(request)
            except Exception:
                client_socket.close()
                return

            # Relay the data back to the client
            while True:
                data = server_socket.recv(4096)
                if data:
                    client_socket.sendall(data)
                else:
                    break
            server_socket.close()
    except Exception as e:
        print("Error handling client:", e)
    finally:
        client_socket.close()


def main():
    listen_addr = '0.0.0.0'
    listen_port = 8080
    proxy_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    proxy_server.bind((listen_addr, listen_port))
    proxy_server.listen(5)
    print(f"[*] Proxy server listening on {listen_addr}:{listen_port}")

    while True:
        client_sock, addr = proxy_server.accept()
        print(f"[*] Accepted connection from {addr}")
        client_handler = threading.Thread(target=handle_client, args=(client_sock,))
        client_handler.start()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[*] Shutting down the proxy server. Press Enter to exit.")
        input()