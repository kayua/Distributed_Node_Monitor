import sys
from kazoo.client import KazooClient
from lib.interface.channel import Channel
from lib.interface.view import View, print_help


def add_set_servers(hostname, username, password):

    file_servers = open("servers/server_list.log", "a+")
    new_server = hostname + ":" + username + ":" + password + "-"
    file_servers.write(new_server)
    file_servers.close()


def get_set_servers():

    file_servers = open("servers/server_list.log", "r")
    list_servers = file_servers.read().split("-")
    return list_servers[:-1]


def install_servers(hostname, user, password):

    channel = Channel()

    if channel.connect(hostname, user, password):

        return True

    channel.install_monitor()
    channel.remote_access("", sudo=True)


def install_client(hostname, user, password):

    channel = Channel()

    if channel.connect(hostname, user, password):

        return True

    channel.install_monitor()


def create_settings_servers(list_servers):

    zookeeper_settings_pointer = open("settings/config.txt", "+a")
    zookeeper_settings_pointer.write("\n")

    for i in range(len(list_servers)):

        zookeeper_server = "server." + str(i + 1) + "=" + list_servers[i] + ":2888:3888\n"
        zookeeper_settings_pointer.write(zookeeper_server)

    zookeeper_settings_pointer.close()


def start_servers():

    saved_nodes = get_set_servers()
    hostname_list = []
    username_list = []
    password_list = []

    print("\n     Starting Servers: \n")

    for i in saved_nodes:

        hostname_list.append(i.split(":")[0])
        username_list.append(i.split(":")[1])
        password_list.append(i.split(":")[2])

    host_list = ":2181,".join(hostname_list)+":2181"
    create_settings_servers(hostname_list)

    for i in range(len(hostname_list)):

        channel = Channel()
        print("         - " + hostname_list[i] + " Started")
        channel.connect(hostname_list[i], username_list[i], password_list[i])
        channel.send_file("settings/config.txt", "monitor/apache-zookeeper-3.6.1/conf/zoo.cfg")
        channel.remote_start_daemon(str(i), host_list, "kayua")



def main():

    print("")
    view = View()
    view.print_view()
    print_help()
    print("Saved Servers:", end=" ")

    saved_nodes = get_set_servers()

    for i in saved_nodes:
        print(i.split(":")[0], end=" ")

    print("\n")

    while True:

        commands = input('Command >> ')
        commands = commands.split(" ")

        if commands[0] == "exit":
            return 1

        elif commands[0] == "ServerInstall":

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

            start_servers()


if __name__ == '__main__':
    sys.exit(main())
