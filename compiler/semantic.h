#ifndef SEMANTIC_H
#define SEMANTIC_H

#include "compiler_common.h"
#include "symbol_table.h"

extern int semanticErrors;

void initSemantic();
int analyzeInstruction(const ILInstruction *inst);
void semanticReport();

#endif