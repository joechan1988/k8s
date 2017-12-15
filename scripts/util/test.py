import common


def test_remote_shell():
    rsh = common.RemoteShell(ip="192.168.1.203", user="root", password="123456")
    if rsh.connect()!=False:
        print("111")

    ret = rsh.execute("hostname")
    print(ret)


def main():
    test_remote_shell()




if __name__ == '__main__':
    main()
