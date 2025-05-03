# Overlord

**Overlord** is a fast, distributed orchestrator for FreeBSD jails oriented to GitOps. You define a file with the service intended to run on your cluster and deployment takes seconds to minutes.

## Architecture

Overlord distributes projects using a chaining system. In the configuration file of the API server, a group of chains pointing to other API servers is defined. The other API servers can define more chains, sharing more and more resources to deploy new projects.

```
                  bravo
                 /
 main <---> alpha
                 \
                  charlie <---> delta
```

The client defines its deployment file by specifying the entry points for deploying the project. Since Overlord recursively performs HTTP requests to each API server to get the labels, the client can specify where to deploy based on the labels.

Assume that only `charlie` and `delta` have the `db-only` label. To deploy projects to the API servers with the specified labels, the client must make an HTTP request to `main`, specifying the chain `alpha.charlie` and `alpha.charlie.delta`. This is done transparently and does not require user intervention.

```
    main . alpha . charlie

              &

 main . alpha . charlie . delta
```

## Features

* Tree chain architecture
* Everything is code!
* Scales very well
* Good for small and large deployments (aka homelab / aka large-enterprise)
* TLS support
* SkyDNS integration (service discovery)
* Auto scaling - let **Overlord** automatically scale your projects!
* VM support - deploy virtual machines anywhere!
* HAProxy / Data Plane API integration (load balancer)
* appConfigs - Templates everywhere!

## Documentation

* [Wiki](https://github.com/DtxdF/overlord/wiki)
