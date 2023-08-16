TARGETS:= xsens
OBJLIBS	= xspublic
INCLUDE=-I. -Ixspublic
CFLAGS=-g $(INCLUDE)
CXXFLAGS=-std=c++11 $(CFLAGS)
LFLAGS=-Lxspublic/xscontroller -Lxspublic/xscommon -Lxspublic/xstypes -lxscontroller -lxscommon -lxstypes -lpthread -lrt -ldl -lpaho-mqtt3as -lpaho-mqttpp3

.PHONY: $(OBJLIBS)
all : $(OBJLIBS) $(TARGETS)

xspublic :
	$(MAKE) -C xspublic $(MFLAGS)

xsens: xsens.o

$(TARGETS):
	$(CXX) $(CFLAGS) $(INCLUDE) $^ -o $@ $(LFLAGS)

%.cpp.o: %.cpp
	$(CXX) -c $(CXXFLAGS) $< -o $@


clean :
	-$(RM) $(OBJECTS) $(TARGETS)
	-$(RM) *.o
