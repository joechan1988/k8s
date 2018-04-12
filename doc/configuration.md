# 沃云容器平台后端部署---配置说明

## 一、文件说明

### 1. 缺省路径
/etc/kde/cluster.yml

### 2. 文件格式

配置文件格式为标准yaml文件格式。建议部署前对文件进行yaml校验。

### 3. 配置项校验

部署过程中会有部分配置项校验，并弹出提示。

## 二、配置项说明

### 请参考如下模板生成cluster.yml并放置到缺省目录：

```
log_level: info  # 日志输出级别，可选项为：debug,info,warning,error,critical

FQDN: "k8s.wocloud.org"  # API访问域名，如果API仅提供内部主机访问则无需设置。
                                设置错误会导致外部主机获取时会报SSL认证错误
external_VIP: "1.1.1.1"  # API访问虚拟IP，如果不通过外部负载均衡访问API则无需设置

nodes:
  - hostname: k8s-master1  #节点主机名，无强制校验，作为日志标识使用
    role: [control,etcd]   #节点角色类型：
                               1.control： 控制节点
                               2.etcd： etcd组建部署节点
                               3.worker： 工作节点
                               
    external_IP: "192.168.1.203"  #节点对外访问网卡的IP
    ssh_user: "root"        # SSH登陆用户名
    ssh_password: "123456"   # SSH登陆密码


kubernetes:
  version: "1.8.0"   #kubernetes版本
  service_cidr: "10.254.0.0/16"     # kubernetes service 虚拟IP 
  cluster_cidr: "172.30.0.0/16"     # Pod CIDR 地址段
  node_port_range: "30000-50000"      # kubernetes service 外部访问端口范围
  cluster_kubernetes_svc_ip: "10.254.0.1"   # kubernetes API 内部IP
  cluster_dns_svc_ip: "10.254.0.2"      # kubernetes DNS服务 虚拟IP
  cluster_dns_domain: "cluster.local."      # kubernetes DNS服务顶级域名
  config_directory: "/etc/kubernetes/"      # kubernetes 配置文件目录
  kubelet_data_directory: "/home/var/lib/kubelet/"  #kubelet组件数据目录，需要保持所在分区空间充足


# 以下Etcd配置暂时保持默认，部分功能还在开发中...
etcd:
  cluster_type: "new"  # 集群类型，默认new为新建
  discovery_type: "local" # public,local,local_etcd
  discovery_url: "https://discovery.etcd.io/new?size={size}"
  ssl: "yes"
  keyfile: "/etc/etcd/ssl/etcd-key.pem"
  cafile: "/etc/etcd/ssl/ca.pem"
  certfile: "/etc/etcd/ssl/etcd.pem"
  data_directory: "/var/lib/etcd/"

cni:
  plugin: "calico"  # CNI组建类型，可选项：flannel,calico。暂时保持默认选项calico  
  flannel:  # Flannel相关配置，如选用其他组件可忽略
    etcd_prefix: /kubernetes/network
  calico:   # calico 相关配置，如选用其他组件可忽略
    ip_autodetection_method: can-reach=192.168.1.1  # IP地址需要改为集群内节点可访问的外部IP地址或网关地址

admin_kubeconfig: "/etc/kde/auth/admin.kubeconfig"  # kubernetes管理员配置文件，kubectl操作集群时需要指定此路径


# 以下配置项还在开发中，请保持默认...
binaries:
  download_url: ""
  path: "/tmp/bin/"
  redownload: "no"
  list:
    - "kube-apiserver"
    - "kubectl"
    - "kubelet"
    - "kube-controller-manager"
    - "etcd"
    - "etcdctl"
    - "flanneld"
    - "kube-scheduler"
    - "kube-proxy"
    - "mk-docker-opts.sh"

images:
  path: ""

 ```


