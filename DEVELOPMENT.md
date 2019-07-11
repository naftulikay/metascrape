# Development

`metascrape` was developed on Python 3.7, and uses `zc.buildout` for dependency management and project dependency
isolation.

## Getting Started

To setup a local development environment, use one of the following methods:

 - Use Vagrant: `vagrant up`
 - Use Docker: `docker build -t naftulikay/metascrape:latest .`
 - Use a local Python development environment.

If you're using Vagrant or a local Python development environment, run the following to set up the project:

```
$ pip install --user -r requirements.txt
$ buildout
```

If you're using `virtualenv`, you can omit the `--user` above.

## Metadata Service Proxying

SSH port-forwarding can be used to expose a remote server's metadata service locally:

```
$ ssh -L 8080:169.254.169.254:80 my-remote-host
```

This will expose the metadata service on local port 8080.

If you need to test from within Docker or Vagrant, you will likely need to forward the port again into the container
or VM.

For Vagrant:

```
$ vagrant ssh -- -R 8080:localhost:8080
```

This will forward port 8080 on localhost in the VM to 8080 on the host, which is where the previous command proxies
the metadata service to.

For Docker, the simplest way to forward is to run the container as `--net host`, but be aware that `--net host` has
many dangerous security implications for running in any other environment than a development environment.
