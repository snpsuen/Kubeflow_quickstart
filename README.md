## Kubeflow Quickstart

In this lab, we will walk you through the steps of uplifting a sample Pytorch deep learning notebook to Kubeflow on a shoestring, so to speak:
* Minimal Kubeflow ecosystem: Kubeflow Pipeline + Kubeflow Trainer V2
* Small footprint: Kind Kubernetes(1.32 or later) on a compute instance or VM, etc of 4GB memory and 20GB free disk space
* A working Pytorch notebook on Google Colab or Jupyter

The exercise may serve as a entry template for future extension to other Kubflow compoents like Katib, Model Registry or more complicated train jobs,

### TL; DR

![Kubeflow_shoestring](kubeflow_shoestring.png)

Sequence of the steps to go through:
1. Install Kubeflow Pipeline and Kubeflow Trainer V2
2. Down a chosen Pytorch notebook as a python script
3. Containerize the python script in a docker
4. Define the Kubeflow Trainer CRDs Trainjob and Trainingruntime
5. Prepare a docker image for the task of creating the Trainjob and Trainingruntime CRDs
6. Write a KFP script to define a Kubeflow pipleline job
7. Sort out RBAC beteen Kubeflow pipeline and Kubeflow Trainer
8. Upload the pipeline manifest via the Kubeflow Pipeline UI and run the pipeline

Build the server program from the source code in source/popen_server_ns.c.
```
gcc -o pop_server_ns popen_server_ns.c
```

### Deploy a backend pod 

The docker image of the pod is based on a well known swiss army knife style container for network troubleshooting, https://github.com/nicolaka/netshoot/.
More specifically, the binaries of the namespacepopen(3) server and crictl are copied to the docker image.
```
cat > Dockerfile <<END
FROM nicolaka/netshoot
COPY ./crictl /bin
COPY ./popen_server_ns /bin
USER root
CMD ["sleep", "infinity"]
END

docker build -t snpsuen/backend_popen:v2 -f Dockerfile .
```
The backend docker is then pulled to run as a kubernetes pod customised with two additional properties.
*  set hostPID to true to allow the node to shared its entire process tree with the pod.
*  mount a host path of /run to provide a runtime container endpoint for crictl.
```
kubectl run backender --image=snpsuen/backend_popen:v2 \
--overrides '
{
  "spec": {
    "containers": [
	  {
	    "image": "snpsuen/backend_popen:v2",
        "name": "backender",
	    "securityContext": {"privileged": true},
		"volumeMounts": [
          {
            "mountPath": "/run",
            "name": "run-volume"
          }
        ]
      }
    ],
    "hostPID": true,
	 "volumes": [
      {
        "name": "run-volume",
        "hostPath": {
          "path": "/run"
        }
      }
    ]
  }
}' -- sleep "infinity"
```
### Deploy a frontend pod 

Use kubectl to run a frontend pod on the fly on Kubernetes based on another swiss army knife docker sample, https://github.com/leodotcloud/swiss-army-knife.

```
kubectl run frontender --image=leodotcloud/swiss-army-knife -- sleep infinity
```
### Deploy a client pod 

Compile and link the popen(3) client program from the source in source/popen_client.c.
```
gcc -o popen_client popen_client.c
```
Create a docker image for the client pod that by copying the binaries of the client program to the busybox image, https://hub.docker.com/_/busybox.
```
cat > Dockerfile <<END
FROM busybox:latest
COPY ./popen_client /bin
CMD ["sleep", "infinity"]
END

docker build -t snpsuen/busypopenclient:v1 -f Dockerfile .
```
Spin up the client pod by running it directly on the newly built docker image on kubernetes.
```
kubectl run busyclient2 --image=snpsuen/busypopenclient:v2
```
### Try out the whole thing

Deploy the backend, frontend and client pods on Kubernetes.
```
keyuser@ubunclone:~$ kubectl run backender --image=snpsuen/backend_popen:v2 \
--overrides '
{
  "spec": {
    "containers": [
          {
            "image": "snpsuen/backend_popen:v2",
        "name": "backender",
            "securityContext": {"privileged": true},
                "volumeMounts": [
          {
            "mountPath": "/run",
            "name": "run-volume"
          }
        ]
      }
    ],
    "hostPID": true,
         "volumes": [
      {
        "name": "run-volume",
        "hostPath": {
          "path": "/run"
        }
      }
    ]
  }
}'
pod/backender created
keyuser@ubunclone:~$ kubectl run frontender --image=leodotcloud/swiss-army-knife -- sleep infinity
pod/frontender created
keyuser@ubunclone:~$ kubectl run busyclient2 --image=snpsuen/busypopenclient:v2
pod/busyclient2 created
```
Observe that the backend and frontend pods are running on the same K8s node, namely ambient-worker2.
```
keyuser@ubunclone:~$ kubectl get pods -o wide
NAME          READY   STATUS    RESTARTS   AGE     IP           NODE              NOMINATED NODE   READINESS GATES
backender     1/1     Running   0          3m46s   10.244.1.3   ambient-worker2   <none>           <none>
busyclient2   1/1     Running   0          2m30s   10.244.1.5   ambient-worker2   <none>           <none>
frontender    1/1     Running   0          2m56s   10.244.1.4   ambient-worker2   <none>           <none>
keyuser@ubunclone:~$
```
Execute the popen(3) server on the backend pod, with the frontend pod set to frontender. Note the TCP port number of the server is set arbitarily to 42855.
```
keyuser@ubunclone:~$ kubectl exec -it backender -- bash
backender:~# popen_server_ns frontender &
[1] 1536
backender:~# WARN[0000] runtime connect using default endpoints: [unix:///run/containerd/containerd.sock unix:///run/crio/crio.sock unix:///var/run/cri-dockerd.sock]. As the default settings are now deprecated, you should set the endpoint instead.
WARN[0000] image connect using default endpoints: [unix:///run/containerd/containerd.sock unix:///run/crio/crio.sock unix:///var/run/cri-dockerd.sock]. As the default settings are now deprecated, you should set the endpoint instead.
WARN[0000] runtime connect using default endpoints: [unix:///run/containerd/containerd.sock unix:///run/crio/crio.sock unix:///var/run/cri-dockerd.sock]. As the default settings are now deprecated, you should set the endpoint instead.
Server is listening to port no. 42855
backender:~#
```
Verify that the popen(3) server listens to port 42855 on the frontend pod instead of the backend pod.
```
keyuser@ubunclone:~$ kubectl exec -it frontender -- sh
# ss -ntlp
State           Recv-Q            Send-Q                        Local Address:Port                        Peer Address:Port
LISTEN          0                 5                                   0.0.0.0:42855                            0.0.0.0:*
#
# exit
keyuser@ubunclone:~$
keyuser@ubunclone:~$ kubectl exec -it backender -- bash
backender:~# ss -ntlp
State         Recv-Q          Send-Q                   Local Address:Port                   Peer Address:Port         Process
backender:~#
backender:~# exit
exit
keyuser@ubunclone:~$
```
Execute the popen(3) client on the client pod by setting the service endpoint to the frontend pod and port number to 42855.
```
keyuser@ubunclone:~$ kubectl exec -it busyclient2 -- sh
/ #
/ # popen_client 10.244.1.4 42855
Enter remote command or "quit":>>
```
Issue remote commands to client program and receive their results from the popen(3) server. Observe that the commands are actually executed on the backend pod.
```
Enter remote command or "quit":>> hostname
Wrote 9 bytes to socket ...
Output from request hostname 2>&1:
backender

Output from request ends.
Enter remote command or "quit":>> ps -ef
Wrote 7 bytes to socket ...
Output from request ps -ef 2>&1:
PID   USER     TIME  COMMAND
    1 root      0:00 {systemd} /sbin/init
   97 root      0:00 /lib/systemd/systemd-journald
  113 root      0:03 /usr/local/bin/containerd
  189 root      0:06 /usr/bin/kubelet --bootstrap-kubeconfig=/etc/kubernetes/bootstrap-kubelet.conf --kubeconfig=/etc/kubernetes/kubelet.conf --config=/var/lib/kubelet/config.yaml --container-runtime-endpoint=unix:///run/containerd/containerd.sock --node-ip=172.18.0.3 --node-labels= --pod-infra-container-image=registry.k8s.io/pause:3.9 --provider-id=kind://docker/ambient/ambient-worker2 --runtime-cgroups=/system.slice/containerd.service
  282 root      0:03 /usr/local/bin/containerd-shim-runc-v2 -namespace k8s.io -id 24bfecd21319fb5392a0d21c11acbc76a1bf3272839e9503dc3a072df6a8f4fd -address /run/containerd/containerd.sock
  288 root      0:00 /usr/local/bin/containerd-shim-runc-v2 -namespace k8s.io -id 61137f999a43fa6b3d6d61023ef2e1e5173ebb110326aed4704dadb0ded391e9 -address /run/containerd/containerd.sock
  354 root      0:01 /usr/local/bin/containerd-shim-runc-v2 -namespace k8s.io -id 771b0dbe334124dc01ad1770041dff727cdb2c0843b0e210e4909b2896020c21 -address /run/containerd/containerd.sock
  381 root      0:01 /usr/local/bin/containerd-shim-runc-v2 -namespace k8s.io -id 30ae1abc8ce9236cc81084fd9d16f529741421d9ad4b0e2af8af8096f7518c1c -address /run/containerd/containerd.sock
  400 65535     0:00 /pause
  416 root      0:10 /usr/local/bin/containerd-shim-runc-v2 -namespace k8s.io -id 25879e97fae3b741809bf8336ca0d7d137194eb594f40a42d38e3c11f9329a0a -address /run/containerd/containerd.sock
  418 65535     0:00 /pause
  454 65535     0:00 /pause
  470 65535     0:00 /pause
  497 65535     0:00 /pause
  532 root      0:00 /usr/local/bin/kube-proxy --config=/var/lib/kube-proxy/config.conf --hostname-override=ambient-worker2
  634 root      0:00 /bin/kindnetd
  645 root      0:01 /coredns -conf /etc/coredns/Corefile
  657 root      0:01 install-cni --log_output_level=default:info,cni:info
 1059 root      0:02 /speaker --port=7472 --log-level=info
 1148 root      0:12 /usr/local/bin/containerd-shim-runc-v2 -namespace k8s.io -id 60f25394451d00fee6c04e352d25ba9e6131bffb3ee912cc6ac93d2ece4fd85f -address /run/containerd/containerd.sock
 1167 65535     0:00 /pause
 1201 root      0:00 sleep infinity
 1288 root      0:06 /usr/local/bin/containerd-shim-runc-v2 -namespace k8s.io -id 2ff3633977975a8253e2b0bb8b1cc342fbe9b1722e74973fe435cedee4c93869 -address /run/containerd/containerd.sock
 1308 65535     0:00 /pause
 1341 root      0:00 sleep infinity
 1400 root      0:01 /usr/local/bin/containerd-shim-runc-v2 -namespace k8s.io -id af2132ecf3f91dbcf34a105c246b014d5987e07a6cfa55967d8ffcbcaf3e8f83 -address /run/containerd/containerd.sock
 1423 65535     0:00 /pause
 1457 root      0:00 sleep infinity
 1536 root      0:00 {ld-musl-x86_64.} ld-linux-x86-64.so.2 --argv0 popen_server_ns --preload /lib/libgcompat.so.0  -- /bin/popen_server_ns frontender
 1597 root      0:00 sh
 1615 root      0:00 popen_client 10.244.1.4 42855
 1616 root      0:00 {ld-musl-x86_64.} ld-linux-x86-64.so.2 --argv0 popen_server_ns --preload /lib/libgcompat.so.0  -- /bin/popen_server_ns frontender
 1617 root      0:00 [hostname]
 1618 root      0:00 [ls]
 1619 root      0:00 ps -ef

Output from request ends.
Enter remote command or "quit":>> ip -4 addr
Wrote 11 bytes to socket ...
Output from request ip -4 addr 2>&1:
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
Error: Peer netns reference is invalid.
Error: Peer netns reference is invalid.
2: eth0@if3: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default  link-netnsid 0
    inet 10.244.1.3/24 brd 10.244.1.255 scope global eth0
       valid_lft forever preferred_lft forever

Output from request ends.
Enter remote command or "quit":>> quit
/ #
```


