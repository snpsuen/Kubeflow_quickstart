## Kubeflow Quickstart

In this lab, we will walk you through the steps of uplifting a sample Pytorch deep learning notebook to Kubeflow on a shoestring, so to speak:
* Minimal Kubeflow ecosystem: Kubeflow Pipelines + Kubeflow Trainer V2
* Small footprint: Kind Kubernetes(1.32 or later) on a compute instance or VM, etc of 4GB memory and 20GB free disk space
* A working Pytorch notebook on Google Colab or Jupyter

The exercise may serve as a entry template for future extension to other Kubflow compoents like Katib, Model Registry or more complicated train jobs.

### TL; DR

![Kubeflow_shoestring](kubeflow_shoestring.png)

### Step by step walk through

1. Install Kubeflow Pipelines and Kubeflow Trainer V2
2. Download a chosen Pytorch notebook as a python script
3. Containerize the python script in a docker
4. Define the Kubeflow Trainer CRDs Trainjob and Trainingruntime
5. Prepare a docker image for the task of creating the Trainjob and Trainingruntime CRDs
6. Write a KFP script to define a Kubeflow pipleline job
7. Sort out RBAC beteen Kubeflow pipeline and Kubeflow Trainer
8. Upload the pipeline manifest and run the pipeline on the Kubeflow Pipeline UI

#### 1. Install Kubeflow Pipeline and Kubeflow Trainer V2 as standalone components

Install Kubeflow Piplines according to the [official guide](https://www.kubeflow.org/docs/components/pipelines/operator-guides/installation/).

```
export PIPELINE_VERSION=2.4.0
kubectl apply -k "github.com/kubeflow/pipelines/manifests/kustomize/cluster-scoped-resources?ref=$PIPELINE_VERSION"
kubectl wait --for condition=established --timeout=60s crd/applications.app.k8s.io
kubectl apply -k "github.com/kubeflow/pipelines/manifests/kustomize/env/dev?ref=$PIPELINE_VERSION"
```

Heads up: When installing from the offical repo, the peristent volume claim (PVC) is set to 20GB each for the mino and mysql pods on the Kubeflow Pipelines control plane. As an alternative, version 2.4.0 of the offical repo is cloned into my github account with the PVC reduced to 10GB each for both pods. It is served at the master branch here. If necessary, you may opt to install the custom repo as follows.

```
kubectl apply -k "github.com/snpsuen/kubeflow-pipelines/manifests/kustomize/cluster-scoped-resources?ref=master"
kubectl wait --for condition=established --timeout=60s crd/applications.app.k8s.io
kubectl apply -k "github.com/snpsuen/kubeflow-pipelines/manifests/kustomize/env/platform-agnostic?ref=master"
```

Install Kubeflow Trainer according to the [official guide](https://www.kubeflow.org/docs/components/trainer/operator-guides/installation/).

```
kubectl apply --server-side -k "https://github.com/kubeflow/trainer.git/manifests/overlays/manager?ref=master"
kubectl apply --server-side -k "https://github.com/kubeflow/trainer.git/manifests/overlays/runtimes?ref=master"
```

#### 2. Download a chosen Pytorch notebook as a python script

A [simple Pytorch notebook](artifact/Pytorch_RNN_LSTM_AT_example05.ipynb) is provided by this repo as an example for the lab. It is adapted from a Pytorch script written by Adrian Tam to train an LSTM DL model to predict about the number of airline passengers in a time series [(see here)](https://machinelearningmastery.com/lstm-for-time-series-prediction-in-pytorch/).

You may upload the notebook sample to Google Colab or Juypter and download it as a python script by clicking *File->Download as* on the UI. The script is also found as [pytorch_rnn_lstm_at_example05.py](artifact/pytorch_rnn_lstm_at_example05.py) in the artifact directory of this repo

#### 3. Containerize the python script in a docker

To be continued ...


