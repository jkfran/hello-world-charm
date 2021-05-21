# hello-world

## Description

Simple K8s charm, it deploys a docker image and listen on port 80.

## Environment

To ease the development, I suggest you to setup a microk8s environment:

```bash
snap install juju --classic
snap install microk8s --classic
snap install charmcraft --beta
microk8s enable dns storage
juju bootstrap microk8s micro
juju add-model hello-world
```

## Usage

```bash
charmcraft build
juju deploy ./hello-world.charm --resource site-image=tutum/hello-world:latest
```

It may take a while to have the deployment finished, in the meantime you can check the status by running:

```bash
juju status
```
