CC=gcc
CFLAGS=
DEPS = utecho.h

%.o: %.c $(DEPS)
	$(CC) -c -o $@ $< $(CFLAGS)

utecho: utecho.o tcp_echo.o udp_echo.o
	$(CC) -o utecho utecho.o tcp_echo.o udp_echo.o

