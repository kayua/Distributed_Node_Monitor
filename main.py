import sys
import time
from datetime import datetime
from kazoo.client import KazooClient
from lib.interface.channel import Channel
from lib.interface.view import View
from lib.interface.view import print_help

DEFAULT_SERVER_LOGS = "servers/server_list.log"
DEFAULT_SETTINGS = "settings/config.txt"
DEFAULT_ZOOKEEPER_SETTINGS = "monitor/apache-zookeeper-3.6.1/conf/zoo.cfg"


def add_set_servers(hostname, username, password):

    file_servers = open(DEFAULT_SERVER_LOGS, "a+")
    new_server = hostname + ":" + username + ":" + password + "-"
    file_servers.write(new_server)
    file_servers.close()


def get_set_servers():

    file_servers = open(DEFAULT_SERVER_LOGS, "r")
    list_servers = file_servers.read().split("-")
    return list_servers[:-1]


def install_servers(hostname, user, password):

    channel = Channel()

    if channel.connect(hostname, user, password):

        return True

    channel.install_monitor()
    channel.remote_access("")


def install_client(hostname, user, password):

    channel = Channel()

    if channel.connect(hostname, user, password):

        return True

    channel.install_monitor()


def create_settings_servers(list_servers):

    zookeeper_settings_pointer = open(DEFAULT_SETTINGS, "+a")
    zookeeper_settings_pointer.write("\n")

    for i in range(len(list_servers)):

        zookeeper_server = "server." + str(i + 1) + "=" + list_servers[i] + ":2888:3888\n"
        zookeeper_settings_pointer.write(zookeeper_server)

    zookeeper_settings_pointer.close()


def get_date_hour():

    return str(datetime.today())


def register_metadata(hosts, num_servers):

    print("\n     Creating registers of session")

    zookeeper_client = KazooClient(hosts=hosts, read_only=True)
    zookeeper_client.start()

    if not zookeeper_client.exists("/number_clients"):

        zookeeper_client.create("/number_clients", b"0")

    number_servers_byte = num_servers.encode("utf-8")

    if not zookeeper_client.exists("/number_servers"):

        zookeeper_client.create("/number_servers", number_servers_byte)

    print("\n         - Create data struct in Servers")

    for i in range(int(num_servers)):

        server_name = "/server" + str(i+1)

        if not zookeeper_client.exists(server_name):

            zookeeper_client.create(server_name, b"False")

    print("\n         - Synchronizing server nodes")

    if not zookeeper_client.exists("/signal_sync"):

        zookeeper_client.create("/signal_sync", b"False")

    if not zookeeper_client.exists("/server_hour"):

        zookeeper_client.create("/server_hour", get_date_hour().encode('utf-8'))


def clear_metadata(hosts):

    print("     Remove registers of session")

    zookeeper_client = KazooClient(hosts=hosts, read_only=True)
    zookeeper_client.start()
    number_clients, _ = zookeeper_client.get("/number_clients")

    for i in range(0, int(number_clients.decode("utf-8"))):

        client_name = "/client" + str(i)
        zookeeper_client.delete(client_name, recursive=True)

    number_servers, _ = zookeeper_client.get("/number_servers")

    zookeeper_client.delete("/number_servers", recursive=True)

    for i in range(0, int(number_servers.decode("utf-8"))):

        server_name = "/server" + str(i)
        zookeeper_client.delete(server_name, recursive=True)

    zookeeper_client.delete("/number_servers", recursive=True)
    zookeeper_client.delete("/signal_sync", recursive=True)
    zookeeper_client.delete("/server_hour", recursive=True)


def start_servers():

    saved_nodes = get_set_servers()
    hostname_list, username_list, password_list = [], [], []

    for i in saved_nodes:

        hostname_list.append(i.split(":")[0])
        username_list.append(i.split(":")[1])
        password_list.append(i.split(":")[2])

    host_list = ":2181,".join(hostname_list) + ":2181"

    create_settings_servers(hostname_list)

    for i in range(len(hostname_list)):

        channel = Channel()
        print("         - " + hostname_list[i] + " Starting Zookeeper server")
        channel.connect(hostname_list[i], username_list[i], password_list[i])
        channel.send_file(DEFAULT_SETTINGS, DEFAULT_ZOOKEEPER_SETTINGS)
        channel.remote_start_zookeeper(str(i+1), host_list, password_list[i])

    time.sleep(20)

    for i in range(len(hostname_list)):

        channel = Channel()
        print("         - " + hostname_list[i] + " Starting monitor")
        channel.connect(hostname_list[i], username_list[i], password_list[i])
        channel.remote_start_monitors(str(i+1), host_list, password_list[i])

    register_metadata(host_list, str(len(hostname_list)))
    print("\n")


def stop_servers():

    saved_nodes = get_set_servers()
    hostname_list, username_list, password_list = [], [], []

    print("\n     Starting Servers: \n")

    for i in saved_nodes:

        hostname_list.append(i.split(":")[0])
        username_list.append(i.split(":")[1])
        password_list.append(i.split(":")[2])

    host_list = ":2181,".join(hostname_list) + ":2181"

    for i in range(len(hostname_list)):

        channel = Channel()
        print("         - " + hostname_list[i] + " Stopping")
        channel.connect(hostname_list[i], username_list[i], password_list[i])
        channel.remove_stop_daemon(str(i), host_list, password_list[i])

    clear_metadata(host_list)
    print("\n")


def remove_servers():

    saved_nodes = get_set_servers()
    hostname_list, username_list, password_list = [], [], []

    print("\n     Starting Servers: \n")

    for i in saved_nodes:

        hostname_list.append(i.split(":")[0])
        username_list.append(i.split(":")[1])
        password_list.append(i.split(":")[2])

    host_list = ":2181,".join(hostname_list) + ":2181"

    for i in range(len(hostname_list)):

        channel = Channel()
        print("         - " + hostname_list[i] + " Stopping")
        channel.connect(hostname_list[i], username_list[i], password_list[i])
        channel.remove_stop_daemon(str(i), host_list, password_list[i])

    clear_metadata(host_list)
    print("\n")


def init_view():

    print("")
    view = View()
    view.print_view()
    print_help()
    print("Saved Servers:", end=" ")

    saved_nodes = get_set_servers()

    for i in saved_nodes:
        print(i.split(":")[0], end=" ")

    print("\n")


def choice_command(commands):

    if commands[0] == "ServerInstall":

        print("\n     Please wait: Installing")

        if install_servers(commands[-3], commands[-2], commands[-1]):

            print("\n     Installation Error\n")

        else:

            print("\n     Successfully Installation\n")
            add_set_servers(commands[-3], commands[-2], commands[-1])

    elif commands[0] == "ClientInstall":

        print("\n     Please wait: Installing")

        if install_client(commands[-3], commands[-2], commands[-1]):
            print("\n     Installation Error\n")

    elif commands[0] == "ServerStart":

        print("\n     Starting Servers: \n")
        start_servers()

    elif commands[0] == "ServerStop":

        print("\n     Stopping Servers: \n")
        stop_servers()

    elif commands[0] == "ServerUninstall":

        print("\n     Stopping Servers: \n")
        remove_servers()

    elif commands[0] == "exit":

        exit(0)


def main():

    init_view()

    while True:

        commands = input('Command > ')
        commands = commands.split(" ")
        choice_command(commands)


if __name__ == '__main__':
    sys.exit(main())
