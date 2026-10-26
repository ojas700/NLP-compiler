#ifndef PARSER_H
#define PARSER_H

#include "compiler_common.h"

int parseLine(const char *line, int line_no, ILInstruction *inst);

#endif