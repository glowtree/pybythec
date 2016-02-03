
#include "../../shared/include/StaticLib.h"
#include "../../shared/include/DynamicLib.h"
#include <iostream>

int main(int argc, char * argv[])
{
  StaticLib sl;
  DynamicLib dl;
  
  std::cout << "running the executable and " << sl.print() << " and " << dl.print() << std::endl;
  return 0;
}
