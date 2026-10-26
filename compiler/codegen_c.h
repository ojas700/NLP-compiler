#ifndef CODEGEN_C_H
#define CODEGEN_C_H

#include "compiler_common.h"

int generateCCode(const ILInstruction instructions[], int count, const char *output_filename);

#endif
