CC=gcc
DEPS = utecho.h

.PHONY: clean


utecho: utecho.c udp_echo.c tcp_echo.c $(DEPS)
	$(CC) -o '$@' utecho.c udp_echo.c tcp_echo.c $(DEPS) 

clean:
	rm utecho
