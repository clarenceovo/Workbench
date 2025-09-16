CXX = g++
CXXFLAGS = -std=c++20 -O2
OBJS = TimeUtil.o SwapArbStrategyBot.o main.o

all: main

TimeUtil.o: TimeUtil.cpp TimeUtil.h
	$(CXX) $(CXXFLAGS) -c TimeUtil.cpp

SwapArbStrategyBot.o: SwapArbStrategyBot.cpp SwapArbStrategyBot.h TimeUtil.h
	$(CXX) $(CXXFLAGS) -c SwapArbStrategyBot.cpp

main.o: main.cpp SwapArbStrategyBot.h TimeUtil.h
	$(CXX) $(CXXFLAGS) -c main.cpp

main: $(OBJS)
	$(CXX) $(CXXFLAGS) -o main $(OBJS)

clean:
	rm -f $(OBJS) main

.PHONY: all clean
