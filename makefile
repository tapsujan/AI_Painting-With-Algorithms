C = g++
CFLAGS = -std=c++23 -Wall -g

LDFLAGS = -lm
TARGET = exe

SRCS = SimulatedAnnealing.cpp stroke.cpp

OBJS = $(SRCS:.cpp=.o)

all: $(TARGET)

$(TARGET): $(OBJS)
	$(C) $(CFLAGS) -o $(TARGET) $(OBJS) $(LDFLAGS)

%.o: %.cpp
	@echo "Compilando . . ."
	$(C) $(CFLAGS) -c $< -o $@

clean:
	@echo "Limpiando . . ."
	rm -f $(OBJS)

testCall.o: testCall.cpp stroke.h

stroke.o: stroke.cpp stroke.h stb_image.h stb_image_write.h

.PHONY: all clean