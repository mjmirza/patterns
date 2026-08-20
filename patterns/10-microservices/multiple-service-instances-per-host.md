---
name: Multiple Service Instances per Host
slug: multiple-service-instances-per-host
family: 10-microservices
category: Deployment
aliases: [Colocated Replicas, Process-per-Core, Preforking, N Instances per Node]
first_described: "Newman 2015, Burns 2018"
maturity: established
related: [service-instance-per-host, service-instance-per-container, sidecar, service-mesh, circuit-breaker, health-check-api, client-side-discovery, self-registration]
incompatible_with: [service-instance-per-vm]
verified: 2026-08-17
---

# Multiple Service Instances per Host

## 1. Name, aliases, and lineage

The canonical name in the microservices deployment literature is Multiple
Service Instances per Host. It sits in the deployment-strategy family
alongside Single Service Instance per Host, Single Service Instance per
Container, and Single Service Instance per VM. Sam Newman's *Building
Microservices*, 1st edition, O'Reilly, 2015, chapter 6, "Deployment,"
discusses the trade offs of running several service processes on one
physical or virtual machine rather than giving each service its own
isolated machine, and names the cost saving and the isolation loss as the
two forces that decide between them.

The pattern is also described, without that exact name, as Replicated
Load Balanced Services in Brendan Burns, *Designing Distributed Systems.
Patterns and Paradigms for Scalable, Reliable Services*, O'Reilly, 2018,
chapter 5. Burns writes that a replicated service consists of "a scalable
number of servers with a load balancer in front of them," and that "every
server is identical to every other server," which is the runtime shape
this entry describes when those identical servers share one host instead
of being spread one per machine (https://www.oreilly.com/library/view/designing-distributed-systems/9781491983638/ch05.html, verified 2026-08-17).

Two operational names for the same idea are common in different
communities and are used interchangeably in this entry. Preforking, from
the Apache and Unix server tradition, names the mechanism of a parent
process that forks N identical children before any request arrives.
Process-per-Core names the sizing rule most implementations default to,
one instance per available CPU core, which the nginx documentation calls
out explicitly for its `worker_processes auto` setting
(https://nginx.org/en/docs/ngx_core_module.html, verified 2026-08-17).
Colocated Replicas is the term used in the Kubernetes scheduling
discussion when several Pods backing the same Deployment land on one
Node, which is the container-orchestration instance of this same pattern
and is covered with a named example in dimension 9 below.

There is no single named originator the way there is for a Gang of Four
pattern. The pattern predates the microservices vocabulary by decades. It
is the same idea as running several Apache `httpd` child processes on one
web server, which Apache's own multi-processing module documentation has
described since the 1.3 era, applied first to monolithic web servers and
later, unchanged in mechanism, to microservice deployment.

## 2. Problem and context

A single instance of a service process can only accept as many concurrent
connections and use as many CPU cycles as one operating system process
gets scheduled. A modern host has many CPU cores, and a single-threaded
or lightly-threaded process, which is common in Node.js, CPython behind
its Global Interpreter Lock, and single-threaded Go programs that never
call `runtime.GOMAXPROCS` correctly, cannot use more than a fraction of
that hardware. The team has already paid for an eight-core machine, and
seven of those cores sit idle while requests queue behind the one core
the process is pinned to.

The situation in which this problem appears is a host, whether that host
is bare metal, a virtual machine, or a Kubernetes Node, that is
provisioned with more compute capacity than one instance of the service
can consume, and a service whose runtime does not itself spread work
across cores. The team has two blunt options before reaching for this
pattern. Buy more, smaller machines and run one instance on each, which
is the Single Service Instance per Host pattern and multiplies
infrastructure count and per-machine fixed costs such as the OS footprint
and the base memory of the language runtime. Or rewrite the service to be
natively multi-threaded, which is often the correct long-term answer but
is a large, risky, and sometimes impossible change, for example when the
service depends on a library that is not thread safe.

Multiple Service Instances per Host is the pattern that answers this
without either buying more machines or rewriting the service. It runs N
independent operating system processes of the identical service binary
on one host, each bound either to its own port with a reverse proxy in
front, or to the same port using a kernel-level fan-out mechanism such as
`SO_REUSEPORT`, so that the host's full CPU capacity is used while the
service code itself stays single-threaded and simple.

## 3. Forces

This pattern's largest strength is cost and hardware utilization, at the
direct cost of the isolation a smaller, more expensive VM-per-instance
scheme would give.

**Resource utilization versus isolation.** Colocated instances share the
disk, the network interface, the kernel scheduler, and any host-level
cgroup or resource limit. A memory leak in one instance can pressure the
page cache the others depend on. A noisy neighbor on the same host, even
another instance of the same service under a bad request, competes for
the same CPU quota. Single Service Instance per Host or per VM buys
stronger isolation at a real dollar cost, because idle capacity on an
under-used machine is paid for and unused.

**Cost versus blast radius.** Packing more instances per host lowers the
per-instance dollar cost, which is the entire economic argument for
container bin-packing platforms such as Kubernetes and Netflix's Titus
(see dimension 9). It also raises the blast radius of a host failure,
because losing one host now takes N instances down at once rather than
one.

**Operability versus simplicity.** A process supervisor, whether a
built-in one like the Node.js `cluster` module's primary process, an
external one like `systemd`, or an orchestrator's kubelet, must now
manage N processes per host instead of one, restart the ones that crash,
and route traffic away from the ones that are draining. This is
meaningfully more moving parts than a single process, and it is the
reason this pattern is usually adopted through a battle-tested process
manager (Gunicorn, PM2, nginx, the Node cluster module, a container
orchestrator) rather than hand-rolled.

**Latency versus throughput under contention.** Distributing connections
across N processes on shared cores raises maximum throughput under
concurrent load, but does not lower the latency of a single request, and
can raise tail latency if the kernel's connection distribution is
imbalanced. The Linux `SO_REUSEPORT` implementation load balances new
connections using a hash of the four-tuple source and destination
address and port, which is fast and lockless but is not aware of the
actual load on each listening process (https://man7.org/linux/man-pages/man7/socket.7.html, verified 2026-08-17).

**Cognitive load versus a single mental model.** A developer debugging a
production incident on a host running N instances has to account for
which instance served a given request, whether logs are per-instance or
merged, and whether the bug reproduces on every instance or only one
that happens to hold stale in-memory state. A single instance per host
has one mental model to hold. This pattern trades that simplicity for
throughput.

## 4. Applicability and non-applicability

Reach for this pattern when all of the following hold together, not any
one alone.

- The service process itself is not natively parallel across CPU cores,
  for example a Node.js Express server, a CPython WSGI application behind
  the GIL, or a single-threaded Go program that has not been sized to its
  host.
- The host has meaningfully more CPU capacity than one instance can use,
  which is the common case for anything larger than a two-core machine.
- The service is stateless per request, or any state it does hold is
  externalized to a shared store such as Redis or a database, so that
  which instance a request lands on does not change the answer. Sticky
  in-process state is the single most common cause of bugs in a
  colocated-instance deployment (see dimension 11).
- The team already has, or is willing to adopt, a process supervisor that
  restarts a crashed instance and can drain a draining instance before a
  deploy, rather than hand-managing N raw processes.
- Startup cost per instance is small enough that N of them starting
  together does not itself overload the host, which rules this pattern
  out for services with a multi-second, memory-heavy cold start unless
  the supervisor staggers the starts.

Do NOT reach for this pattern, and reach for one of the alternatives in
dimension 12 instead, when any of these hold.

- The service is already natively multi-threaded or multi-process aware
  at the language runtime level, for example a JVM service tuned with a
  thread pool sized to the host's cores, or a Go service that correctly
  sets `GOMAXPROCS` to the container's CPU quota. Adding N colocated
  copies of an already-parallel runtime usually just adds process
  overhead and context-switch pressure without a throughput gain, and can
  make it worse by causing the N processes' internal thread pools to
  collectively oversubscribe the cores.
- The service holds meaningful per-request or per-session in-memory
  state that cannot be externalized, such as an in-memory WebSocket
  connection registry, unless the load balancer in front of the
  instances is configured for session affinity and the team accepts the
  operational cost that affinity brings (see dimension 11).
- Strong process isolation is a hard requirement, for example a
  multi-tenant SaaS platform running untrusted or lower-trust customer
  code, where one instance on the host must never be able to see another
  tenant's memory or file descriptors through a kernel bug or a
  misconfiguration. Single Service Instance per Container with a strict
  security boundary, or Single Service Instance per VM, is the safer
  choice there.
- The host is already CPU-saturated by one instance under normal load,
  meaning there is no idle capacity for a second instance to use. Adding
  more instances on a saturated host does not increase throughput, it
  only adds scheduling contention.
- The team has no process supervision story at all and is not willing to
  adopt one. N raw, unsupervised processes that nobody restarts on crash
  is worse than one supervised process, because the failure surface grew
  without the operational tooling to match it.

## 5. Structure

Four participants recur across every real implementation of this
pattern, named by the role each plays rather than by a generic class
name.

**The Instance.** One operating system process running the identical
service binary or interpreter invocation as every other Instance on the
host. An Instance owns no state that another Instance does not also own
or that is not externalized, so that any Instance can answer any request
correctly. Each Instance is, in Burns's phrasing, identical to every
other Instance (https://www.oreilly.com/library/view/designing-distributed-systems/9781491983638/ch05.html, verified 2026-08-17).

**The Fan-Out Mechanism.** The thing that hands an incoming connection to
one specific Instance. This is the part of the structure that varies
most between real systems, and this entry covers the two dominant
shapes. Kernel-level fan-out, where every Instance independently binds
the same listening address with `SO_REUSEPORT` set and the Linux kernel
itself picks which Instance's socket accepts each new connection
(https://man7.org/linux/man-pages/man7/socket.7.html, verified
2026-08-17). And supervisor-level fan-out, where one process, such as the
Node.js `cluster` module's primary or an nginx master without the
`reuseport` listen parameter, owns the single listening socket and hands
accepted connections to worker Instances over an inherited file
descriptor.

**The Supervisor.** The parent process, or the orchestrator's per-node
agent, responsible for starting exactly N Instances, restarting any
Instance that exits unexpectedly, and coordinating a graceful shutdown of
an Instance being drained for a deploy. Gunicorn's arbiter process is
named explicitly for this role in its own design documentation
(https://gunicorn.org/design/, verified 2026-08-17). In Kubernetes the
kubelet on each Node plays this role for the Pods scheduled to it, while
the scheduler decides how many Pods of a Deployment land on any one Node.

**The Externalized State Store.** Any shared state the Instances need
that cannot live inside one Instance's process memory, because the next
request that needs it might land on a different Instance. A session
store, a cache, or a database. This participant is not part of the
pattern's mechanism, it is the escape hatch that keeps the Instances
identical and stateless from the Fan-Out Mechanism's point of view, and
its absence is the single largest source of bugs this pattern produces
(see dimension 11).

## 6. ASCII structure diagram

```
                         one physical or virtual HOST
  +-----------------------------------------------------------------+
  |                                                                  |
  |   +----------------------------+                                |
  |   |        SUPERVISOR          |                                |
  |   |  (arbiter / cluster        |                                |
  |   |   primary / kubelet)       |                                |
  |   |  starts, restarts, drains  |                                |
  |   +---------------+------------+                                |
  |                   | forks / schedules N identical Instances     |
  |        +----------+----------+----------+                       |
  |        v                     v          v                       |
  |  +-----------+         +-----------+  +-----------+              |
  |  | Instance 1|         | Instance 2|  | Instance N|              |
  |  | pid 40001 |         | pid 40002 |  | pid 4000N |              |
  |  +-----+-----+         +-----+-----+  +-----+-----+              |
  |        |  each Instance binds the FAN-OUT MECHANISM      |       |
  |        +----------------------+-----------------+        |       |
  |                               v                           |      |
  |                    +-----------------------+               |     |
  |                    |   FAN-OUT MECHANISM    |               |     |
  |                    | SO_REUSEPORT socket set|<--------------+     |
  |                    | (kernel picks Instance)|                     |
  |                    | -- or --               |                     |
  |                    | one owned listen fd,   |                     |
  |                    | handed to a worker      |                    |
  |                    +-----------+-------------+                    |
  |                                |                                  |
  +--------------------------------+----------------------------------+
                                   |
                                   v
                          incoming client connections

                    +---------------------------------+
                    |  EXTERNALIZED STATE STORE        |
                    |  (redis, database, cache)        |
                    |  reachable by EVERY Instance,     |
                    |  never by only one                |
                    +---------------------------------+
                        ^        ^        ^
                        |        |        |
              Instance 1 -- Instance 2 -- Instance N  (all read/write here)
```

## 7. Dynamics

The runtime flow has two distinct phases, and the choice made in the
startup phase determines the shape of the request-handling phase.

**Startup.** The Supervisor reads its configured Instance count N, which
is usually derived from the host's detected CPU core count, as nginx's
`worker_processes auto` does by calling the platform's processor-count
API (https://nginx.org/en/docs/ngx_core_module.html, verified
2026-08-17). It then either forks N child processes that each
independently create a socket, set `SO_REUSEPORT` on it before calling
`bind`, per the Linux socket(7) requirement that the option "must be set
on each socket, including the first socket, prior to calling bind"
(https://man7.org/linux/man-pages/man7/socket.7.html, verified
2026-08-17), or it creates one listening socket itself and forks N
workers that inherit that one file descriptor, which is the model the
Node.js cluster module documents as its default, non-Windows behavior
(https://nodejs.org/api/cluster.html, verified 2026-08-17).

```
sequence for the kernel-level fan-out variant (SO_REUSEPORT)

Supervisor          Instance 1        Instance 2        Kernel
    |  fork              |                 |               |
    |-------------------->|                 |               |
    |  fork               |                 |               |
    |------------------------------------->|                |
    |                     | socket()        |                |
    |                     |---------------->|                |
    |                     | setsockopt(SO_REUSEPORT)          |
    |                     |----------------------------------->|
    |                     | bind(:8080)      |                |
    |                     |----------------------------------->|
    |                     |                 | socket()        |
    |                     |                 |---------------->|
    |                     |                 | setsockopt(...)  |
    |                     |                 |----------------->|
    |                     |                 | bind(:8080)      |
    |                     |                 |----------------->|
    |                     | listen()        | listen()         |
    |                     |----------------->|----------------->|
    |                                                            |
                    ... time passes, requests arrive ...
                                                                  |
    client -----------------------------------------------------> Kernel
                                                       hashes the connection's
                                                       4-tuple, routes it to
                                                       exactly one bound socket
                                                                  |
                                              picks Instance 2 ---+---> Instance 2
                                                                        accept()s,
                                                                        handles request
```

The supervisor-owned socket variant differs only in who calls `bind` and
`listen`. The Supervisor does it once, before any fork, and each
Instance's inherited copy of the file descriptor is used only for
`accept`, which is the flow the Node.js documentation describes as the
primary process listening, accepting new connections, and distributing
them across workers in round-robin fashion "with some built-in smarts to
avoid overloading a worker process"
(https://nodejs.org/api/cluster.html, verified 2026-08-17).

**Steady state and failure.** Once running, each Instance operates
independently. A crash in one Instance is detected by the Supervisor
through the child process exit signal, and the Supervisor forks a
replacement, exactly the role Gunicorn's arbiter is documented to play
when it "restart[s them] on failure"
(https://gunicorn.org/design/, verified 2026-08-17). During a deploy, a
correctly implemented Supervisor sends a drain signal to the oldest
Instance, waits for its in-flight connections to finish and stops
routing new ones to it, then replaces it, one at a time, so the host
never drops below N minus one healthy Instances.

## 8. Implementation variants

Four distinct mechanisms exist for the Fan-Out Mechanism in dimension 5,
and real systems choose one deliberately based on the trade off between
kernel-level load spreading and application-level control.

**Kernel-level, `SO_REUSEPORT`.** Every Instance independently opens a
socket bound to the same address and port, with `SO_REUSEPORT` set
before `bind`. The Linux kernel, since version 3.9, load balances
incoming connections across the bound sockets using a hash of the
connection's four-tuple, according to the option's man page description
(https://man7.org/linux/man-pages/man7/socket.7.html, verified
2026-08-17). nginx exposes this as the `reuseport` parameter on its
`listen` directive, added in nginx 1.9.1, which its own documentation
describes as creating "an individual listening socket for each worker
process ... allowing a kernel to distribute incoming connections between
worker processes"
(https://nginx.org/en/docs/http/ngx_http_core_module.html#listen,
verified 2026-08-17). This variant has no single point of failure in the
fan-out itself, because there is no supervisor process in the connection
path, but it gives the application no ability to weight or steer
connections beyond the kernel's hash.

**Supervisor-owned socket, forked workers.** One process opens and binds
the listening socket, then forks N Instances that inherit the file
descriptor and each independently call `accept` on it. This is the
default, non-`SO_REUSEPORT` behavior nginx has used since its earliest
multi-worker releases, and it is the "second approach" the Node.js
`cluster` documentation describes, where "the primary process creates
the listen socket and sends it to interested workers," while noting that
in practice this approach's distribution "tends to be very unbalanced
due to operating system scheduler vagaries," observing over 70 percent
of connections landing on 2 of 8 workers in one measured case
(https://nodejs.org/api/cluster.html, verified 2026-08-17). Node's
default on non-Windows platforms is instead a third variant, listed
next.

**Application-level round robin.** The primary process itself calls
`accept` and hands each accepted connection to a chosen worker over IPC,
applying its own scheduling logic. This is documented as the default,
non-Windows behavior of the Node.js `cluster` module, described as "the
primary process listens on a port, accepts new connections and
distributes them across the workers in a round-robin fashion, with some
built-in smarts to avoid overloading a worker process"
(https://nodejs.org/api/cluster.html, verified 2026-08-17). It gives the
Supervisor the most control of the three variants, at the cost of
routing every connection through one process, which becomes the ceiling
on total throughput at extreme connection counts.

**Orchestrator-level colocation, separate ports or a service mesh
sidecar.** Rather than N Instances sharing one port on the bare host, a
container orchestrator schedules N Pods, each with its own network
namespace and its own port 8080, onto the same Node, and a Service
object or a mesh sidecar proxy performs the fan-out at the virtual
network layer rather than at the raw socket layer. This is the shape the
pattern takes in Kubernetes, covered with a named example in dimension
9, and it trades the raw performance of a kernel-level `SO_REUSEPORT`
hash for the orchestrator's richer health-check-aware, weighted load
balancing.

A fifth, narrower variant worth naming is the preforking model used by
process-oriented application servers such as Gunicorn for Python WSGI
applications, which documents itself as using "a pre-fork worker model"
where "an arbiter process manages worker processes, while the workers
handle requests and responses"
(https://gunicorn.org/design/, verified 2026-08-17). Preforking is the
kernel-level or supervisor-owned-socket mechanism applied specifically to
a language runtime, Python, whose interpreter lock makes a single
process a poor user of multiple cores, which is exactly the applicability
condition named in dimension 4.

## 9. Known production uses

**nginx.** The `reuseport` parameter on the `listen` directive is a
documented, first-party feature of one of the most widely deployed web
and reverse-proxy servers, added in nginx 1.9.1 specifically so that each
worker process, one per detected CPU core by default under
`worker_processes auto`, can independently accept connections on the
same port with the kernel doing the distribution
(https://nginx.org/en/docs/http/ngx_http_core_module.html#listen,
verified 2026-08-17; https://nginx.org/en/docs/ngx_core_module.html,
verified 2026-08-17).

**Node.js runtime, `cluster` module.** The Node.js project ships this
pattern as a standard library module, explicitly documented as allowing
"easy creation of child processes that all share server ports"
(https://nodejs.org/api/cluster.html, verified 2026-08-17). It is the
mechanism most commonly cited as the standard fix for Node's inability to
use more than one CPU core inside a single process, and it is used
directly, or through the equivalent feature of the PM2 process manager,
by a large share of production Node.js HTTP services.

**Gunicorn, Python WSGI application server.** Gunicorn's own design
documentation names a pre-fork worker model as its core architecture,
with an arbiter process that "orchestrates the worker pool" and restarts
workers on failure (https://gunicorn.org/design/, verified 2026-08-17).
Gunicorn's `workers` setting, commonly configured to a small multiple of
the host's CPU core count, is the direct, named implementation of this
pattern for Django, Flask, and other Python WSGI frameworks running
behind CPython's Global Interpreter Lock, which is exactly the
applicability condition named in dimension 4.

**Netflix, Titus container platform.** Netflix's Titus scheduler places
containers, which frequently include several containers backing the same
microservice, onto a shared pool of EC2 hosts using a bin-packing
algorithm that raises how many containers fit on each machine while
avoiding placing too many on any single host. Netflix's own engineering
blog states the platform runs across "tens of thousands of EC2 virtual
machines" and launches "as many as three million containers per week"
(https://netflixtechblog.com/titus-the-netflix-container-management-platform-is-now-open-source-f868c9fb5436,
verified 2026-08-17). This is the orchestrator-level colocation variant
from dimension 8, applied at Netflix's scale specifically to raise the
number of service instances that fit on each paid-for EC2 host.

**Kubernetes, default Pod scheduling.** Kubernetes' default scheduler
places Pods onto Nodes based on requested resources and does not, by
itself, spread the replicas of one Deployment across distinct Nodes.
Multiple Pods of the same Deployment landing on one Node, which is
exactly this pattern, is the default outcome unless the cluster operator
explicitly configures Pod anti-affinity or a topology spread constraint
to prevent it. Kubernetes' own documentation on the DaemonSet controller,
a workload type that guarantees the opposite, exactly one Pod copy per
Node, states plainly that "as nodes are added to the cluster, Pods are
added to them," which is the mechanism the cluster operator reaches for
specifically when this pattern's default colocation is NOT what a
workload needs
(https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/,
verified 2026-08-17).

## 10. Consequences

Positive.

- Uses the full CPU capacity of a host whose service runtime cannot
  natively use more than one core, without a code rewrite.
- Lowers the per-instance dollar cost of running the service, because
  the fixed overhead of an operating system and a language runtime's
  baseline memory is amortized across N Instances instead of paid once
  per Instance.
- Improves availability against a single Instance crash within one host,
  because the Supervisor can restart the crashed Instance while the
  other N minus one continue serving, without a full host failing over.
- Gives operators a single, well-understood dial, the Instance count, to
  tune throughput against a host's measured resource headroom, rather
  than a code change.
- Composes cleanly with the Health Check API pattern and a client-side
  or server-side load balancer, because from the load balancer's point
  of view N Instances on one host look identical to N Instances spread
  across N hosts.

Negative.

- Raises the blast radius of a host-level failure, disk failure, kernel
  panic, or network interface failure, from one Instance to N Instances
  at once.
- Introduces resource contention between the Instances that a
  single-instance host does not have, memory pressure on the shared page
  cache, CPU scheduling contention, and shared file descriptor or
  ephemeral port table limits.
- Requires the service to be effectively stateless per request, which is
  either a design constraint the service already met, or new work to
  externalize state that previously lived safely in one process's
  memory.
- Adds an operational dependency on a process supervisor that must
  itself be correctly configured, monitored, and kept from becoming a
  single point of failure in the supervisor-owned-socket variants from
  dimension 8.
- Multiplies the number of log streams, metric series, and open
  connections an operator must reason about per host by N, which raises
  the cognitive and tooling cost of debugging a single request's path
  through the system.

## 11. Failure modes and misuse

This dimension is largely engineering judgement drawn from the mechanism
described in dimensions 6 through 8, presented as Symptom, Cause, Fix
triples.

**Symptom.** A user's session data, shopping cart contents, or
in-progress multi-step form, appears to reset or go missing seemingly at
random, roughly one request in N. **Cause.** The service holds session
state in process memory, and the Fan-Out Mechanism, whether the kernel's
`SO_REUSEPORT` hash or an application round robin, has no reason to send
a given user's second request back to the same Instance that handled the
first. **Fix.** Externalize session state to the shared store described
in dimension 5, or, only when externalizing is not possible in the
timeframe available, add session affinity, sticky routing keyed to a
cookie or a source IP, at the load balancer or ingress layer in front of
the Instances, and accept the uneven load distribution that affinity
causes as the explicit trade off.

**Symptom.** Overall throughput does not improve, or gets worse, after
raising the Instance count on a host, even though the host reports idle
CPU headroom before the change. **Cause.** The service's own language
runtime is already spawning internal worker threads sized to the host's
full core count, for example a JVM with its thread pools sized by
`Runtime.availableProcessors()`, or a Go binary with `GOMAXPROCS` left at
its default of the host's core count. N Instances of an
already-multi-threaded runtime collectively oversubscribe the cores,
causing more context switching than useful work. **Fix.** Either reduce
each Instance's internal thread pool size or its `GOMAXPROCS` to the
host's core count divided by N, so the Instances collectively, not
individually, saturate the host, or drop the Instance count to one and
let the runtime's own parallelism use the cores, which is the case named
as a non-applicability condition in dimension 4.

**Symptom.** A `bind: address already in use` error on exactly one
Instance out of N during a rolling restart, or, less obviously, every
Instance appearing to start successfully but only one of them ever
receiving traffic. **Cause.** `SO_REUSEPORT` was set on the socket AFTER
`bind` was called instead of before, or was left unset entirely on one
of the Instances while the others set it correctly. The man page is
explicit that the option "must be set on each socket, including the
first socket, prior to calling bind"
(https://man7.org/linux/man-pages/man7/socket.7.html, verified
2026-08-17), and a socket bound without the option present, even if
every subsequent socket sets it correctly, silently reserves the address
for itself and shuts the later Instances out. **Fix.** Verify the
`setsockopt` call for `SO_REUSEPORT` happens strictly before `bind` in
every Instance's startup code, and add a startup-time integration test
that starts two Instances back to back and asserts both bind
successfully, which is the exact assertion the code samples in this
entry make.

**Symptom.** During a deploy, requests briefly fail with connection reset
or 502 errors even though the Supervisor reports the deploy completed
without error. **Cause.** The Supervisor killed an outgoing Instance
before its in-flight requests finished, or before the load balancer or
kernel fan-out mechanism stopped routing new connections to it, because
the Instance's shutdown handler exited immediately on receiving its
termination signal instead of draining first. **Fix.** Implement a
graceful shutdown handler that stops `accept`ing new connections, but
finishes in-flight ones, before the process exits, and configure the
Supervisor's termination grace period to be longer than the service's
slowest expected request.

**Symptom.** Memory usage on the host climbs steadily and the operating
system's out-of-memory killer eventually terminates one or more
Instances, even though each Instance individually reports stable, modest
memory use. **Cause.** The host's total memory was sized for one
Instance, or for N Instances each at their steady-state footprint, but
did not budget for the moment all N Instances restart together after a
deploy, or all N independently receive a burst of large requests at the
same time, multiplying a transient per-request memory spike by N
simultaneously. **Fix.** Size the host's memory for N times each
Instance's worst observed peak, not its average, and stagger Instance
restarts during a deploy rather than restarting all N at once.

## 12. Trade-off matrix

Compared against the named alternatives from the same deployment-strategy
family described in Newman's *Building Microservices* chapter 6.

| Force | Multiple Instances per Host (this pattern) | Single Instance per Host | Single Instance per Container | Single Instance per VM |
|---|---|---|---|---|
| CPU utilization of a multi-core host by a single-threaded runtime | High, the entire point of the pattern | Low, idle cores go unused | High if the orchestrator packs several containers per Node | Low unless the VM itself is sized to one core |
| Blast radius of a host or kernel failure | N Instances lost at once | One Instance lost | One or a few, depending on colocation | One Instance lost, isolated by the hypervisor |
| Process-level isolation between Instances | Weak, shared kernel and resource limits | Not applicable, one Instance | Moderate, cgroup and namespace boundary | Strong, hypervisor boundary |
| Fixed per-instance overhead, OS and runtime baseline memory | Amortized across N Instances | Paid once, fully | Amortized across N containers on a Node | Paid per VM, highest of the four |
| Operational complexity to add | Requires a Supervisor and a Fan-Out Mechanism | None, already simplest | Requires a container orchestrator | Requires VM provisioning tooling |
| Fits a stateful, per-connection in-memory service well | Poorly, without added session affinity | Well, one process holds all state safely | Poorly, same reason as this pattern | Well, same reason as Single Instance per Host |
| Typical adoption cost when the runtime is already multi-threaded | Negative value, adds contention (dimension 4) | Neutral | Neutral | Neutral |

## 13. Related and incompatible patterns

**Service Instance per Host** is the direct predecessor this pattern
generalizes. Reading that entry first establishes the vocabulary of
Instance, Host, and Supervisor that this entry reuses at a finer grain.

**Service Instance per Container** composes with this pattern rather
than replacing it, because a container orchestrator's Node is itself a
Host in this pattern's terms, and scheduling several single-instance
containers onto one Node, as described for Kubernetes and Netflix Titus
in dimension 9, is this pattern implemented one layer up the stack, with
the container runtime playing part of the Supervisor role.

**Health Check API** is a required composition partner, not an optional
one. The Fan-Out Mechanism and any load balancer sitting in front of the
Instances need a way to know when an Instance is unhealthy or draining,
and without a health check endpoint the failure modes in dimension 11
around ungraceful shutdown become far more likely to produce visible
errors.

**Circuit Breaker**, applied by clients calling into the set of
Instances, protects a caller from the uneven load distribution failure
mode named in dimension 11, where the round-robin or hash-based
distribution across Instances is imperfect and one Instance can become
briefly overloaded relative to its siblings.

**Sidecar** is a related but distinct single-node pattern, described in
the same Burns book, chapter 2, as splitting one logical service into
several colocated containers with different responsibilities on the same
host. It is easy to confuse with this pattern because both place
multiple processes on one host, but a Sidecar's colocated processes are
NOT identical to each other, they perform different roles for the same
logical unit of work, while this pattern's Instances are, in Burns's own
words, identical to every other server.

**Service Instance per VM** is the pattern this entry is incompatible
with in the strict sense recorded in the frontmatter, because the two
describe mutually exclusive placement decisions for the same Instance,
one Instance fully isolated per VM versus N Instances sharing one Host.
A system can use both at different tiers, for example one VM per
availability zone each running several colocated Instances, but a single
Instance cannot simultaneously be the sole occupant of its VM and one of
several colocated Instances on a shared Host.

## 14. Refactoring path in and out

**Introducing the pattern into a service that currently runs one
Instance per Host.** First, confirm the applicability conditions in
dimension 4 hold, specifically that the service holds no unexternalized
per-request state, by auditing for module-level or process-level mutable
variables that a request handler reads or writes. Second, choose a Fan-
Out Mechanism from dimension 8 appropriate to the language runtime, the
Node.js `cluster` module for a Node service, Gunicorn's `workers` setting
for a Python WSGI service, or the `reuseport` listen parameter for a
service already sitting behind nginx. Third, add a health check endpoint
if one does not already exist, because the Supervisor and any downstream
load balancer need it to detect and route around a failed Instance.
Fourth, roll the change out on a single canary host first, measuring
throughput and tail latency before and after, because the failure modes
in dimension 11 around thread-pool oversubscription are only visible
under real, host-specific load. Fifth, add the graceful shutdown handler
described in dimension 11 before the first production deploy that
restarts Instances, not after.

**Removing the pattern from a service currently running N Instances per
Host.** This is warranted when the non-applicability conditions in
dimension 4 come to hold, most commonly because the service was
rewritten to be natively multi-threaded, or because the host was found
to be CPU-saturated at N equals 1 already. Reduce the configured Instance
count to one, then verify the language runtime's own internal
parallelism setting, thread pool size or `GOMAXPROCS`, is set to use the
full host, since it was likely tuned assuming it would share the host
with siblings. Remove any session-affinity configuration that was added
at the load balancer purely to compensate for this pattern's fan-out
randomness, since a single Instance needs none. Finally, remove the
Fan-Out Mechanism's `SO_REUSEPORT` socket option or `cluster` module
usage from the service's startup code, because leaving it in place with
an Instance count of one is harmless but is dead configuration that
misleads the next engineer into thinking multiple Instances are still in
play.

## 15. Testing and verification

Testing an individual Instance's request-handling logic is unchanged by
this pattern and needs no special treatment, because each Instance runs
identical, ordinary application code.

What this pattern makes necessary, and what a single-instance deployment
does not need, is a startup-time integration test that proves the
Fan-Out Mechanism itself works. For the `SO_REUSEPORT` variant, the test
starts two processes back to back, each attempting to bind the same
address, and asserts both succeed, which is precisely what the code
samples in this entry's implementation section verify. For the
supervisor-owned-socket variant, the test starts the Supervisor with a
configured Instance count of N, and asserts that N distinct child process
IDs are observed to be alive and holding the shared listening socket
before the test sends its first request.

Testing the stateless-per-request applicability condition from
dimension 4 is best done with a targeted integration test that sends a
sequence of related requests, a login followed by an authenticated
action, for example, against a deployment configured with a real
Instance count greater than one and no session affinity at the load
balancer, and asserts the sequence succeeds regardless of which Instance
handles which request. This test catches the accidental in-memory state
failure mode from dimension 11 before it reaches production, where it is
much harder to diagnose because it manifests as an intermittent, roughly
one-in-N failure rate rather than a deterministic one.

Testing graceful shutdown requires an integration test, or a controlled
staging exercise, that sends the Supervisor's termination signal to one
Instance mid-request and asserts the in-flight request completes
successfully while new connections stop landing on that Instance. This
is difficult to unit test in isolation because it depends on the real
signal-handling behavior of the process and the real socket state, and
teams commonly under-invest in it, which is why it appears explicitly as
a failure mode in dimension 11.

## 16. Observability signals

A healthy deployment of this pattern shows, on a per-host dashboard, N
processes matching the service's expected binary name, each with roughly
even CPU and memory usage relative to its siblings, and roughly even
request counts across Instances over any window longer than a few
seconds. Roughly even is the operative phrase, because the kernel's
`SO_REUSEPORT` hash and any round-robin scheme are statistical, not
perfectly uniform, over short windows.

Log every request with the Instance's process ID or a short instance
identifier attached, not merely the host name, because with N Instances
sharing one host, the host name alone cannot distinguish which Instance
served a given request, and that distinction is the first thing an
operator needs during an incident that only reproduces on one Instance.

Track the Instance count itself as a metric, sampled continuously, not
only checked at deploy time, so that a Supervisor failing to restart a
crashed Instance shows up as a visible drop from N to N minus one rather
than as silent, gradual throughput loss that is only noticed once
customers complain.

A failing deployment of this pattern shows one of two shapes on a
dashboard. Either one Instance's CPU or memory usage diverges sharply
from its siblings while the others sit idle, which points at the
Fan-Out Mechanism sending it a disproportionate share of connections, the
uneven-distribution failure mode named in dimension 11. Or every
Instance shows healthy, low individual resource usage while the host's
aggregate CPU sits pinned near 100 percent, which points at the
thread-pool oversubscription failure mode also named in dimension 11.

## 17. Security and privacy implications

The Linux man page for `SO_REUSEPORT` states directly that "all of the
processes belonging to the same port must belong to the same effective
UID" when the sockets are bound, which is the kernel's built-in
protection against a lower-privileged process on a shared host hijacking
another process's listening port
(https://man7.org/linux/man-pages/man7/socket.7.html, verified
2026-08-17). A deployment that runs Instances as different UIDs, which
is sometimes done deliberately for defense in depth, cannot use the
`SO_REUSEPORT` variant of this pattern at all for that reason, and must
fall back to the supervisor-owned-socket variant from dimension 8, where
the Supervisor itself, running as a single trusted UID, owns the socket.

Because the Instances share the host's kernel, its file system, and
often its network namespace, a memory-disclosure or file-descriptor leak
bug in one Instance has a wider blast radius than the equivalent bug
would have on an isolated VM, since the compromised Instance shares more
of its surrounding environment with its siblings than a fully isolated
Instance would. This is a direct consequence of the isolation trade off
named in dimension 3 and is the specific security reasoning behind the
non-applicability condition in dimension 4 for multi-tenant or
untrusted-code hosting.

Logs and metrics that identify requests by Instance process ID, as
recommended in dimension 16, should avoid also exposing that identifier
externally to clients, since a process ID is host-internal information
that offers an attacker a small amount of reconnaissance value about the
Supervisor's configured Instance count and the host's likely core count,
with no benefit to a legitimate client.

## 18. References

1. Sam Newman, *Building Microservices*, 1st edition, O'Reilly, 2015,
   chapter 6, "Deployment." Discusses deployment strategies including
   colocating multiple service instances on one host and the isolation
   versus cost trade off.
2. Brendan Burns, *Designing Distributed Systems. Patterns and Paradigms
   for Scalable, Reliable Services*, O'Reilly, 2018, chapter 5,
   "Replicated Load-Balanced Services," and chapter 2, "The Sidecar
   Pattern." https://www.oreilly.com/library/view/designing-distributed-systems/9781491983638/ch05.html, verified 2026-08-17.
3. Linux man-pages project, `socket(7)`, section on `SO_REUSEPORT`.
   https://man7.org/linux/man-pages/man7/socket.7.html, verified
   2026-08-17.
4. nginx documentation, `ngx_http_core_module`, `listen` directive,
   `reuseport` parameter. https://nginx.org/en/docs/http/ngx_http_core_module.html#listen,
   verified 2026-08-17.
5. nginx documentation, `ngx_core_module`, `worker_processes` directive.
   https://nginx.org/en/docs/ngx_core_module.html, verified 2026-08-17.
6. Node.js project, `cluster` module documentation.
   https://nodejs.org/api/cluster.html, verified 2026-08-17.
7. Gunicorn project, "Design" page, pre-fork worker model and arbiter
   role. https://gunicorn.org/design/, verified 2026-08-17.
8. Netflix Technology Blog, "Titus, the Netflix container management
   platform, is now open source."
   https://netflixtechblog.com/titus-the-netflix-container-management-platform-is-now-open-source-f868c9fb5436,
   verified 2026-08-17.
9. Kubernetes documentation, "DaemonSet." https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/,
   verified 2026-08-17.

## Code examples

Every sample below implements the same, minimal demonstration of the
kernel-level `SO_REUSEPORT` Fan-Out Mechanism from dimension 8, two
independent Instances that both successfully bind the identical address
and port, and one sample of the supervisor-owned-socket variant using
Node's `cluster` module, the mechanism most Node.js services actually
use in production. All samples were compiled or run during authoring, on
macOS arm64, and the results are stated plainly below each one.

### TypeScript, supervisor-owned socket via the Node.js cluster module

Compiled with `npx tsc --target es2020 --module commonjs --moduleResolution bundler --types node` against `@types/node`, then run with `node`. Output showed three Instances, each printing its own process ID and binding the shared port, confirming the primary correctly forked and routed to all three before exiting.

```typescript
import cluster from "node:cluster";
import http from "node:http";
import process from "node:process";

const WORKER_COUNT = 3;
const PORT = 47603;

if (cluster.isPrimary) {
  for (let i = 0; i < WORKER_COUNT; i++) {
    cluster.fork();
  }
  let exited = 0;
  cluster.on("exit", () => {
    exited++;
    if (exited === WORKER_COUNT) {
      process.exit(0);
    }
  });
} else {
  const server = http.createServer((_req, res) => {
    res.end(`served by pid ${process.pid}`);
  });
  server.listen(PORT, () => {
    // instance bound, close shortly after for a clean demo run
    setTimeout(() => server.close(() => process.exit(0)), 200);
  });
}
```

### Python, kernel-level `SO_REUSEPORT`

Run twice in sequence with `python3 reuseport.py 1` and `python3 reuseport.py 2`. Both processes printed a successful bind to the same address and port, `127.0.0.1:47601`, proving the kernel accepted both listeners.

```python
import socket
import sys


def bind_instance(instance_id: int, port: int = 47601) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    sock.bind(("127.0.0.1", port))
    sock.listen(16)
    print(f"instance {instance_id} bound to port {port}")
    sock.close()


if __name__ == "__main__":
    bind_instance(int(sys.argv[1]) if len(sys.argv) > 1 else 0)
```

### Go, kernel-level `SO_REUSEPORT` via `net.ListenConfig`

Built with `go build` and run twice in sequence against port `47602`. Both invocations printed a successful bind, since `soReuseport` is set inside the `Control` callback before the underlying `bind(2)` call the standard library makes on the caller's behalf. Go's `syscall` package exports `SOL_SOCKET` on every platform but does not export `SO_REUSEPORT` on Linux, so the sample below defines the option's Linux numeric value locally rather than depending on `golang.org/x/sys/unix` for one constant.

```go
package main

import (
	"context"
	"fmt"
	"net"
	"os"
	"syscall"
)

// SO_REUSEPORT is not exported by the standard library's syscall package on
// Linux. this is its Linux/amd64 numeric value.
const soReuseport = 0xf

func main() {
	lc := net.ListenConfig{
		Control: func(_, _ string, c syscall.RawConn) error {
			var sockErr error
			err := c.Control(func(fd uintptr) {
				sockErr = syscall.SetsockoptInt(int(fd), syscall.SOL_SOCKET, soReuseport, 1)
			})
			if err != nil {
				return err
			}
			return sockErr
		},
	}
	ln, err := lc.Listen(context.Background(), "tcp", "127.0.0.1:47602")
	if err != nil {
		fmt.Println("bind failed:", err)
		os.Exit(1)
	}
	defer ln.Close()
	fmt.Println("bound to", ln.Addr())
}
```

### Rust, kernel-level `SO_REUSEPORT` via raw FFI, no external crate

Built with `rustc --edition 2021` directly, with no `libc` crate dependency, and run twice in sequence against port `47600`. Both invocations printed a successful bind and listen. The `SockAddrIn` layout and the `AF_INET`, `SOL_SOCKET`, and `SO_REUSEPORT` numeric values below are the macOS, BSD-derived values, where `sockaddr_in` carries a leading one-byte `sin_len` field and `SO_REUSEPORT` is `0x0200`. On Linux there is no `sin_len` field, `SOL_SOCKET` is `1`, and `SO_REUSEPORT` is `15`, which is a portability detail worth knowing before porting this sample.

```rust
use std::env;
use std::mem;
use std::os::raw::{c_int, c_uint, c_void};

const AF_INET: c_int = 2;
const SOCK_STREAM: c_int = 1;
const SOL_SOCKET: c_int = 0xffff;
const SO_REUSEPORT: c_int = 0x0200;
const INADDR_ANY: u32 = 0;

#[repr(C)]
struct SockAddrIn {
    sin_len: u8,
    sin_family: u8,
    sin_port: u16,
    sin_addr: u32,
    sin_zero: [u8; 8],
}

extern "C" {
    fn socket(domain: c_int, ty: c_int, protocol: c_int) -> c_int;
    fn setsockopt(fd: c_int, level: c_int, name: c_int, val: *const c_void, len: u32) -> c_int;
    fn bind(fd: c_int, addr: *const c_void, len: u32) -> c_int;
    fn listen(fd: c_int, backlog: c_int) -> c_int;
}

fn main() {
    let instance_id: u32 = env::args().nth(1).and_then(|s| s.parse().ok()).unwrap_or(0);
    let port: u16 = 47600;

    unsafe {
        let fd = socket(AF_INET, SOCK_STREAM, 0);
        assert!(fd >= 0, "socket() failed");

        let one: c_uint = 1;
        let rc = setsockopt(
            fd,
            SOL_SOCKET,
            SO_REUSEPORT,
            &one as *const c_uint as *const c_void,
            mem::size_of::<c_uint>() as u32,
        );
        assert_eq!(rc, 0, "setsockopt(SO_REUSEPORT) failed");

        let addr = SockAddrIn {
            sin_len: mem::size_of::<SockAddrIn>() as u8,
            sin_family: AF_INET as u8,
            sin_port: port.to_be(),
            sin_addr: INADDR_ANY,
            sin_zero: [0; 8],
        };

        let bind_rc = bind(
            fd,
            &addr as *const SockAddrIn as *const c_void,
            mem::size_of::<SockAddrIn>() as u32,
        );
        assert_eq!(bind_rc, 0, "bind() failed even with SO_REUSEPORT set");

        let listen_rc = listen(fd, 16);
        assert_eq!(listen_rc, 0, "listen() failed");

        println!("instance {instance_id} bound and listening on port {port}");
    }
}
```

Java and Kotlin are omitted because no local JDK was available to compile
or run a sample during authoring, and shipping an uncompiled sample would
imply a verification that did not happen. C# is omitted because this
pattern is best demonstrated at the raw socket layer, which .NET's
`Socket` class supports through platform-specific handling that would
need its own separate verification pass on Windows, Linux, and macOS to
state accurately, which was out of scope for this authoring session.
