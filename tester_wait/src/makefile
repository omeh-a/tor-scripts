CC=gcc
CFLAGS=
DEPS =

%.o: %.c $(DEPS)
	$(CC) -c -o $@ $< $(CFLAGS)

tester_wait: tester_wait.o
	$(CC) -o tester_wait tester_wait.o

