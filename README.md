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

## Goals

Overlord was created to address the shortcomings that [LittleJet](https://github.com/DtxdF/LittleJet) and [cloud-machine](https://github.com/DtxdF/cloud-machine) have. LittleJet is good for small-scale environments, but for large-scale environments like a large enterprise it is limited, especially for scaling depending on how many machines the enterprise has without resorting to a performance penalty.

cloud-machine, although it scales very well, it is difficult to manage VMs, so the problem is usability.

Overlord scales very well, it is easy to manage the projects created by Director, get information about the jails, and offers an API so it can be easily extended.

## Documentation

* `man 1 overlord`
* `man 5 overlord-spec`
* [Wiki](https://github.com/DtxdF/overlord/wiki)
