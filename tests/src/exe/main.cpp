
#include "../StaticLib/StaticElectricity.h"
#include <iostream>

int main(int argc, char * argv[])
{
  StaticElectricity se;
  
  std::cout << "running exe and " << se.print() << std::endl; 

  return 0;
}

