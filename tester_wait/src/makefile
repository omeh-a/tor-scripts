CC=gcc
CFLAGS=
DEPS =

%.o: %.c $(DEPS)
	$(CC) -c -o $@ $< $(CFLAGS)

tester_wait: wai.o
	$(CC) -o tester_wait wait.o

