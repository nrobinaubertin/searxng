<h1 align="center">
    <img src="searxng.svg">
</h1>

<h4 align="center">An operator charm for SearXNG</h4>

## What is SearXNG ?

[SearXNG](https://searxng.org) is a free internet
[metasearch engine](https://en.wikipedia.org/wiki/Metasearch_engine) which
aggregates results from various search services and databases.
Users are neither tracked nor profiled.  

## Usage

This [Juju](https://juju.is/) [charm](https://juju.is/docs/olm/charmed-operators)
must be deployed on a kubernetes substrate.  

You can package the charm using [charmcraft](https://github.com/canonical/charmcraft).

```shell
charmcraft pack
juju deploy ./searxng_ubuntu-22.04-amd64.charm --resource searxng-image='searxng/searxng'
```

After deployment, check the unit's IP with `juju status` and visit it's `8080` port.
