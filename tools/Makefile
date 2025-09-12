CC = gcc
CFLAGS = -Wall -g $(shell pkg-config --cflags libdivecomputer)
LDFLAGS = $(shell pkg-config --libs libdivecomputer)
TARGET = dlf_parser_helper

all: $(TARGET)

$(TARGET): dlf_parser_helper.o
	$(CC) -o $(TARGET) dlf_parser_helper.o $(LDFLAGS)

dlf_parser_helper.o: dlf_parser_helper.c
	$(CC) $(CFLAGS) -c dlf_parser_helper.c

clean:
	rm -f $(TARGET) *.o
