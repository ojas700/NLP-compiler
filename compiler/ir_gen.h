#ifndef IR_GEN_H
#define IR_GEN_H

#include "compiler_common.h"

typedef struct {
    char op[16];
    char arg1[64];
    char arg2[64];
    char result[64];
} Quadruple;

#define MAX_QUADS 1000

extern Quadruple irTable[MAX_QUADS];
extern int irCount;

void initIR();
void generateIR(const ILInstruction instructions[], int count);
void displayIR();

#endif
