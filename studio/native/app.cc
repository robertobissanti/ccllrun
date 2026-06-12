/* app.cc — ccllrun Studio come app macOS a finestra nativa.
 *
 * Al lancio: fork → il FIGLIO esegue il server Python della dashboard
 * (Resources/server.py, col python del venv ~/.ccllrun se esiste); il PADRE
 * attende che la porta risponda e apre una WKWebView puntata alla dashboard.
 * Alla chiusura della finestra il server viene terminato.
 *
 * Struttura del bundle:
 *   ccllrun Studio.app/Contents/MacOS/ccllrun-studio   (questo binario)
 *   ccllrun Studio.app/Contents/Resources/server.py
 *   ccllrun Studio.app/Contents/Resources/web/index.html
 *
 * Headless: STUDIO_NO_WINDOW=1 esegue solo il server (utile per la LAN).
 *
 * Derivato da DStudio di Giuseppe Perrotta (BSD-3-Clause):
 * https://github.com/sk8erboi17/DStudio — vedi LICENSE.DStudio.
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>
#include <signal.h>
#include <libgen.h>
#include <limits.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <sys/wait.h>
#include <sys/stat.h>
#include <mach-o/dyld.h>
#include "webview.h"

static int pick_free_port(int start) {
    for (int p = start; p <= start + 40 && p <= 65535; p++) {
        int fd = socket(AF_INET, SOCK_STREAM, 0);
        if (fd < 0) return start;
        int on = 1;
        setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &on, sizeof on);
        struct sockaddr_in a;
        memset(&a, 0, sizeof a);
        a.sin_family = AF_INET;
        a.sin_port = htons((uint16_t)p);
        inet_pton(AF_INET, "127.0.0.1", &a.sin_addr);
        int ok = bind(fd, (struct sockaddr *)&a, sizeof a) == 0;
        close(fd);
        if (ok) return p;
    }
    return start;
}

static int wait_for_port(int port, int timeout_ms) {
    for (int waited = 0; waited <= timeout_ms; waited += 100) {
        int fd = socket(AF_INET, SOCK_STREAM, 0);
        if (fd < 0) return 0;
        struct sockaddr_in a;
        memset(&a, 0, sizeof a);
        a.sin_family = AF_INET;
        a.sin_port = htons((uint16_t)port);
        inet_pton(AF_INET, "127.0.0.1", &a.sin_addr);
        int r = connect(fd, (struct sockaddr *)&a, sizeof a);
        close(fd);
        if (r == 0) return 1;
        usleep(100 * 1000);
    }
    return 0;
}

/* Directory Resources del bundle (…/Contents/MacOS/exe → …/Contents/Resources),
 * oppure la directory dell'eseguibile quando si lancia il binario nudo. */
static void resources_dir(char *out, size_t cap) {
    char exe[PATH_MAX];
    uint32_t n = sizeof exe;
    if (_NSGetExecutablePath(exe, &n) != 0) { snprintf(out, cap, "."); return; }
    char real[PATH_MAX];
    if (!realpath(exe, real)) strncpy(real, exe, sizeof real - 1);
    char *dir = dirname(real);                 /* …/Contents/MacOS  o  …/studio/native */
    char cand[PATH_MAX];
    snprintf(cand, sizeof cand, "%s/../Resources/server.py", dir);
    struct stat st;
    if (stat(cand, &st) == 0) { snprintf(out, cap, "%s/../Resources", dir); return; }
    snprintf(cand, sizeof cand, "%s/../server.py", dir);   /* lancio da studio/native */
    if (stat(cand, &st) == 0) { snprintf(out, cap, "%s/..", dir); return; }
    snprintf(out, cap, "%s", dir);
}

static pid_t g_server_pid = 0;
static void stop_server(void) {
    if (g_server_pid > 0) { kill(g_server_pid, SIGTERM); g_server_pid = 0; }
}

int main(void) {
    char res[PATH_MAX];
    resources_dir(res, sizeof res);
    char server_py[PATH_MAX];
    snprintf(server_py, sizeof server_py, "%s/server.py", res);

    /* python: venv di ccllrun se esiste (ha aiohttp), altrimenti python3 di sistema */
    char venv_py[PATH_MAX];
    const char *home = getenv("HOME");
    snprintf(venv_py, sizeof venv_py, "%s/.ccllrun/venv/bin/python", home ? home : "");
    struct stat st;
    const char *python = (stat(venv_py, &st) == 0) ? venv_py : "python3";

    const char *env_port = getenv("STUDIO_PORT");
    int port = env_port ? atoi(env_port) : pick_free_port(8770);
    char port_s[16];
    snprintf(port_s, sizeof port_s, "%d", port);
    setenv("STUDIO_PORT", port_s, 1);

    if (getenv("STUDIO_NO_WINDOW")) {
        execlp(python, python, server_py, (char *)NULL);
        perror("exec server.py");
        return 1;
    }

    pid_t pid = fork();
    if (pid < 0) { perror("fork"); return 1; }
    if (pid == 0) {
        execlp(python, python, server_py, (char *)NULL);
        perror("exec server.py");
        _exit(1);
    }
    g_server_pid = pid;
    atexit(stop_server);   /* [NSApp terminate] chiama exit() → fermiamo il server */

    if (!wait_for_port(port, 8000))
        fprintf(stderr, "ccllrun Studio: server non pronto su :%d, apro comunque la finestra\n", port);

    char url[96];
    snprintf(url, sizeof url, "http://127.0.0.1:%d/", port);
    webview_t w = webview_create(1180, 800, "ccllrun Studio");
    webview_navigate(w, url);
    webview_run(w);        /* blocca finché la finestra resta aperta */

    stop_server();
    waitpid(pid, NULL, 0);
    return 0;
}
