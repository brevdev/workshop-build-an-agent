/*
 * netlink-stub.c — LD_PRELOAD shim for the OpenShell sandbox.
 *
 * The sandbox's per-process seccomp filter blocks socket(AF_NETLINK), so
 * getifaddrs()/if_nameindex() fail with EPERM. libzmq calls getifaddrs() during
 * ipykernel startup (src/ip_resolver.cpp) and asserts the list is non-empty,
 * which kills the kernel. This shim intercepts those libc calls and returns a
 * single loopback (lo / 127.0.0.1) interface so ZMQ resolves cleanly without
 * ever touching netlink.
 *
 * It does NOT weaken egress: it only stubs interface ENUMERATION. All actual
 * socket I/O still goes through the sandbox's Landlock/proxy enforcement.
 *
 * Scope: preload ONLY into the Jupyter process tree (kernels).
 * Build: zig cc -shared -fPIC -o netlink-stub.so netlink-stub.c
 */
#define _GNU_SOURCE
#include <ifaddrs.h>
#include <net/if.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <stdlib.h>
#include <string.h>

/* We hand back one interface ("lo", 127.0.0.1/255.0.0.0, IFF_UP|IFF_LOOPBACK).
 * All the memory is allocated in one struct so freeifaddrs() can free it as a
 * no-op-ish single block; we track it with a sentinel so our free matches. */

struct _stub_ifaddr {
    struct ifaddrs ifa;
    struct sockaddr_in addr;
    struct sockaddr_in netmask;
    char name[4];
};

int getifaddrs(struct ifaddrs **ifap) {
    if (!ifap) return -1;
    struct _stub_ifaddr *s = calloc(1, sizeof(struct _stub_ifaddr));
    if (!s) return -1;

    strcpy(s->name, "lo");

    s->addr.sin_family = AF_INET;
    s->addr.sin_addr.s_addr = htonl(0x7f000001); /* 127.0.0.1 */

    s->netmask.sin_family = AF_INET;
    s->netmask.sin_addr.s_addr = htonl(0xff000000); /* 255.0.0.0 */

    s->ifa.ifa_next = NULL;
    s->ifa.ifa_name = s->name;
    s->ifa.ifa_flags = IFF_UP | IFF_LOOPBACK | IFF_RUNNING;
    s->ifa.ifa_addr = (struct sockaddr *)&s->addr;
    s->ifa.ifa_netmask = (struct sockaddr *)&s->netmask;
    s->ifa.ifa_ifu.ifu_broadaddr = NULL;
    s->ifa.ifa_data = NULL;

    *ifap = &s->ifa;
    return 0;
}

void freeifaddrs(struct ifaddrs *ifa) {
    /* ifa points at the .ifa member of our _stub_ifaddr, which is the first
     * member, so the struct base == ifa. Safe to free directly. */
    if (ifa) free(ifa);
}

struct if_nameindex *if_nameindex(void) {
    struct if_nameindex *arr = calloc(2, sizeof(struct if_nameindex));
    if (!arr) return NULL;
    arr[0].if_index = 1;
    arr[0].if_name = strdup("lo");
    arr[1].if_index = 0;
    arr[1].if_name = NULL;
    return arr;
}

void if_freenameindex(struct if_nameindex *ptr) {
    if (!ptr) return;
    for (struct if_nameindex *p = ptr; p->if_name != NULL; p++) {
        free(p->if_name);
    }
    free(ptr);
}
