CXX = g++

CXXFLAGS = -std=c++23 -Wall -O3

TARGET = exe

SRCS = SimulatedAnnealing.cpp stroke.cpp

OBJS = $(SRCS:.cpp=.o)

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CXX) $(CXXFLAGS) -o $(TARGET) $(OBJS)

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

clean:
	rm -f $(OBJS)

SimulatedAnnealing.o: SimulatedAnnealing.cpp stroke.h
stroke.o: stroke.cpp stroke.h stb_image.h stb_image_write.h

.PHONY: all clean