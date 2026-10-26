#include <stdio.h>
#include <string.h>
#include "ir_gen.h"

Quadruple irTable[MAX_QUADS];
int irCount = 0;
static int tempVarCount = 1;
static int labelCount = 1;

void initIR()
{
    irCount = 0;
    tempVarCount = 1;
    labelCount = 1;
}

static void emitQuad(const char *op, const char *arg1, const char *arg2, const char *res)
{
    if (irCount >= MAX_QUADS) return;
    strncpy(irTable[irCount].op, op, sizeof(irTable[irCount].op) - 1);
    strncpy(irTable[irCount].arg1, arg1 ? arg1 : "-", sizeof(irTable[irCount].arg1) - 1);
    strncpy(irTable[irCount].arg2, arg2 ? arg2 : "-", sizeof(irTable[irCount].arg2) - 1);
    strncpy(irTable[irCount].result, res ? res : "-", sizeof(irTable[irCount].result) - 1);
    irCount++;
}

void generateIR(const ILInstruction instructions[], int count)
{
    initIR();
    char labelStack[50][32];
    int labelTop = -1;

    for (int i = 0; i < count; i++) {
        const ILInstruction *inst = &instructions[i];
        switch (inst->type) {
            case CMD_DECLARE:
                emitQuad("DECLARE", inst->arg1, "-", inst->arg2);
                break;

            case CMD_ASSIGN:
                // Check if simple assignment or binary op
                // Format could be: a = b + c
                emitQuad("ASSIGN", inst->arg2, "-", inst->arg1);
                break;

            case CMD_READ:
                emitQuad("READ", "-", "-", inst->arg1);
                break;

            case CMD_PRINT:
                emitQuad("PRINT", "-", "-", inst->arg1);
                break;

            case CMD_IF: {
                char lElse[32], lEnd[32];
                snprintf(lElse, sizeof(lElse), "L_ELSE_%d", labelCount);
                snprintf(lEnd, sizeof(lEnd), "L_ENDIF_%d", labelCount++);
                emitQuad("IF_FALSE", inst->arg1, "GOTO", lElse);
                labelTop++;
                strncpy(labelStack[labelTop], lEnd, 31);
                labelTop++;
                strncpy(labelStack[labelTop], lElse, 31);
                break;
            }

            case CMD_ELSE: {
                if (labelTop >= 1) {
                    char lElse[32], lEnd[32];
                    strncpy(lElse, labelStack[labelTop--], 31);
                    strncpy(lEnd, labelStack[labelTop], 31);
                    emitQuad("GOTO", "-", "-", lEnd);
                    emitQuad("LABEL", "-", "-", lElse);
                }
                break;
            }

            case CMD_END_IF: {
                if (labelTop >= 0) {
                    char lTarget[32];
                    strncpy(lTarget, labelStack[labelTop--], 31);
                    emitQuad("LABEL", "-", "-", lTarget);
                }
                break;
            }

            case CMD_WHILE: {
                char lStart[32], lEnd[32];
                snprintf(lStart, sizeof(lStart), "L_WHILE_START_%d", labelCount);
                snprintf(lEnd, sizeof(lEnd), "L_WHILE_END_%d", labelCount++);
                emitQuad("LABEL", "-", "-", lStart);
                emitQuad("IF_FALSE", inst->arg1, "GOTO", lEnd);
                labelTop++;
                strncpy(labelStack[labelTop], lStart, 31);
                labelTop++;
                strncpy(labelStack[labelTop], lEnd, 31);
                break;
            }

            case CMD_END_WHILE: {
                if (labelTop >= 1) {
                    char lEnd[32], lStart[32];
                    strncpy(lEnd, labelStack[labelTop--], 31);
                    strncpy(lStart, labelStack[labelTop--], 31);
                    emitQuad("GOTO", "-", "-", lStart);
                    emitQuad("LABEL", "-", "-", lEnd);
                }
                break;
            }

            case CMD_FOR: {
                char lStart[32], lEnd[32];
                snprintf(lStart, sizeof(lStart), "L_FOR_START_%d", labelCount);
                snprintf(lEnd, sizeof(lEnd), "L_FOR_END_%d", labelCount++);
                // init loop var
                emitQuad("ASSIGN", inst->arg2, "-", inst->arg1);
                emitQuad("LABEL", "-", "-", lStart);
                char cond[64];
                snprintf(cond, sizeof(cond), "%s <= %s", inst->arg1, inst->arg3);
                emitQuad("IF_FALSE", cond, "GOTO", lEnd);
                // Push onto stack: loop var, start label, end label
                labelTop++;
                strncpy(labelStack[labelTop], inst->arg1, 31);
                labelTop++;
                strncpy(labelStack[labelTop], lStart, 31);
                labelTop++;
                strncpy(labelStack[labelTop], lEnd, 31);
                break;
            }

            case CMD_END_FOR: {
                if (labelTop >= 2) {
                    char lEnd[32], lStart[32], loopVar[32];
                    strncpy(lEnd, labelStack[labelTop--], 31);
                    strncpy(lStart, labelStack[labelTop--], 31);
                    strncpy(loopVar, labelStack[labelTop--], 31);
                    char inc[64];
                    snprintf(inc, sizeof(inc), "%s + 1", loopVar);
                    emitQuad("ASSIGN", inc, "-", loopVar);
                    emitQuad("GOTO", "-", "-", lStart);
                    emitQuad("LABEL", "-", "-", lEnd);
                }
                break;
            }

            default:
                break;
        }
    }
}

void displayIR()
{
    printf("\n========== THREE-ADDRESS CODE (IR) ==========\n");
    printf("%-5s %-12s %-20s %-20s %-15s\n", "No.", "Op", "Arg1", "Arg2", "Result");
    printf("----------------------------------------------------------------------\n");
    for (int i = 0; i < irCount; i++) {
        printf("%-5d %-12s %-20s %-20s %-15s\n",
               i + 1, irTable[i].op, irTable[i].arg1, irTable[i].arg2, irTable[i].result);
    }
    printf("=============================================\n");
}
