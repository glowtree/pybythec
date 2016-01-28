
#include "../../shared/include/StaticLib.h"
#include <iostream>

int main(int argc, char * argv[])
{
  StaticLib se;
  
  std::cout << "running the executable and " << se.print() << std::endl;

  return 0;
}
